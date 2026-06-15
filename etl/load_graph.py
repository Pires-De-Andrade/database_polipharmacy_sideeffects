#!/usr/bin/env python3
"""
==============================================================================
Projeto BD Polifarmácia — ETL: Carga dos CSVs no Neo4j
==============================================================================
Carrega os datasets do DECAGON (SNAP Stanford) no banco de grafos Neo4j.

Uso:
    python load_graph.py                       # carga completa
    python load_graph.py --sample 1000         # apenas primeiras 1000 linhas/CSV
    python load_graph.py --skip-combo          # pula CAUSES_COMBINED (4.65M arestas)
    python load_graph.py --no-constraints      # pula criação de constraints

Variáveis de ambiente (.env):
    NEO4J_URI      (default: bolt://localhost:7687)
    NEO4J_USER     (default: neo4j)
    NEO4J_PASSWORD (default: neo4j)

Dependências:
    pip install -r requirements.txt
==============================================================================
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
from tqdm import tqdm

# ==============================================================================
# Configuração de logging
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ==============================================================================
# Caminhos dos datasets
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CSV_FILES = {
    "ppi":          DATA_DIR / "bio-decagon-ppi.csv",
    "targets":      DATA_DIR / "bio-decagon-targets.csv",
    "combo":        DATA_DIR / "bio-decagon-combo.csv",
    "mono":         DATA_DIR / "bio-decagon-mono.csv",
    "categories":   DATA_DIR / "bio-decagon-effectcategories.csv",
}

# Tamanho do batch para transações Neo4j (rows por tx)
BATCH_SIZE = 1000


# ==============================================================================
# Conexão com Neo4j
# ==============================================================================
def get_driver():
    """Cria driver Neo4j usando variáveis de ambiente."""
    load_dotenv(BASE_DIR / ".env")

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j")

    logger.info("Conectando ao Neo4j %s@%s", user, uri)
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Verificar conectividade
    driver.verify_connectivity()
    logger.info("  Conexão verificada com sucesso.")

    return driver


# ==============================================================================
# Helpers
# ==============================================================================
def read_csv(path, sample=None):
    """Lê um CSV com tratamento de erros e amostragem opcional."""
    if not path.exists():
        logger.error("Arquivo não encontrado: %s", path)
        raise FileNotFoundError(f"CSV não encontrado: {path}")

    logger.info("Lendo %s ...", path.name)
    df = pd.read_csv(path, dtype=str)  # tudo como string inicialmente

    if sample and sample > 0:
        df = df.head(sample)
        logger.info("  → Amostra limitada a %d linhas", sample)

    logger.info("  → %d linhas, %d colunas: %s", len(df), len(df.columns),
                list(df.columns))
    return df


def run_in_batches(driver, data, cypher, batch_size=BATCH_SIZE, label=""):
    """
    Executa um Cypher em batches dentro de transações de escrita.
    `data` é uma lista de dicts, cada dict é passado como parâmetro `rows`.
    """
    total = len(data)
    processed = 0

    with driver.session() as session:
        for i in tqdm(range(0, total, batch_size), desc=f"  [{label}]",
                      unit="batch", disable=total < batch_size):
            batch = data[i : i + batch_size]

            def _write_tx(tx, rows):
                tx.run(cypher, rows=rows)

            session.execute_write(_write_tx, batch)
            processed += len(batch)

    logger.info("  [%s] %d registros processados", label, processed)
    return processed


# ==============================================================================
# Criação de constraints
# ==============================================================================
def create_constraints(driver):
    """Cria constraints de unicidade para os nós do grafo."""
    logger.info("=" * 60)
    logger.info("ETAPA 0: Criando constraints")
    logger.info("=" * 60)

    constraints = [
        ("drug_stitch_unique",
         "CREATE CONSTRAINT drug_stitch_unique IF NOT EXISTS "
         "FOR (d:Drug) REQUIRE d.stitch_id IS UNIQUE"),
        ("protein_gene_unique",
         "CREATE CONSTRAINT protein_gene_unique IF NOT EXISTS "
         "FOR (p:Protein) REQUIRE p.gene_id IS UNIQUE"),
        ("side_effect_cui_unique",
         "CREATE CONSTRAINT side_effect_cui_unique IF NOT EXISTS "
         "FOR (s:SideEffect) REQUIRE s.umls_cui IS UNIQUE"),
    ]

    with driver.session() as session:
        for name, cypher in constraints:
            session.run(cypher)
            logger.info("  ✓ Constraint %s criada/verificada", name)


# ==============================================================================
# Etapas de carga — Nós
# ==============================================================================

def load_drug_nodes(driver, sample=None):
    """
    Cria nós :Drug a partir de todos os STITCH IDs encontrados nos CSVs.
    Usa MERGE para idempotência.
    """
    logger.info("=" * 60)
    logger.info("ETAPA 1: Criando nós :Drug")
    logger.info("=" * 60)

    stitch_ids = set()

    # Targets
    df = read_csv(CSV_FILES["targets"], sample=sample)
    df.columns = ["stitch", "gene"]
    stitch_ids.update(df["stitch"].unique())

    # Combo
    df = read_csv(CSV_FILES["combo"], sample=sample)
    df.columns = ["stitch_1", "stitch_2", "se_cui", "se_name"]
    stitch_ids.update(df["stitch_1"].unique())
    stitch_ids.update(df["stitch_2"].unique())

    # Mono
    df = read_csv(CSV_FILES["mono"], sample=sample)
    df.columns = ["stitch", "se_cui", "se_name"]
    stitch_ids.update(df["stitch"].unique())

    logger.info("  Total de drogas únicas: %d", len(stitch_ids))

    data = [{"stitch_id": sid} for sid in sorted(stitch_ids)]

    cypher = """
        UNWIND $rows AS row
        MERGE (d:Drug {stitch_id: row.stitch_id})
    """
    run_in_batches(driver, data, cypher, label="Drug")


def load_protein_nodes(driver, sample=None):
    """
    Cria nós :Protein a partir dos Gene IDs de PPI e targets.
    Usa MERGE para idempotência.
    """
    logger.info("=" * 60)
    logger.info("ETAPA 2: Criando nós :Protein")
    logger.info("=" * 60)

    gene_ids = set()

    # PPI
    df = read_csv(CSV_FILES["ppi"], sample=sample)
    df.columns = ["gene_1", "gene_2"]
    gene_ids.update(df["gene_1"].astype(int).unique())
    gene_ids.update(df["gene_2"].astype(int).unique())

    # Targets
    df = read_csv(CSV_FILES["targets"], sample=sample)
    df.columns = ["stitch", "gene"]
    gene_ids.update(df["gene"].astype(int).unique())

    logger.info("  Total de proteínas únicas: %d", len(gene_ids))

    data = [{"gene_id": int(gid)} for gid in sorted(gene_ids)]

    cypher = """
        UNWIND $rows AS row
        MERGE (p:Protein {gene_id: row.gene_id})
    """
    run_in_batches(driver, data, cypher, label="Protein")


def load_side_effect_nodes(driver, sample=None):
    """
    Cria nós :SideEffect a partir de effectcategories.csv, combo.csv e mono.csv.
    Usa MERGE para idempotência.
    """
    logger.info("=" * 60)
    logger.info("ETAPA 3: Criando nós :SideEffect")
    logger.info("=" * 60)

    # Mapa completo de efeitos: umls_cui -> (name, category)
    effects = {}

    # Efeitos com categoria
    df_cat = read_csv(CSV_FILES["categories"], sample=sample)
    df_cat.columns = ["umls_cui", "name", "category"]
    for _, row in df_cat.iterrows():
        effects[row["umls_cui"]] = (row["name"], row["category"])

    # Efeitos do combo (podem ter novos)
    df_combo = read_csv(CSV_FILES["combo"], sample=sample)
    df_combo.columns = ["stitch_1", "stitch_2", "se_cui", "se_name"]
    for _, row in df_combo[["se_cui", "se_name"]].drop_duplicates().iterrows():
        if row["se_cui"] not in effects:
            effects[row["se_cui"]] = (row["se_name"], None)

    # Efeitos do mono (podem ter novos)
    df_mono = read_csv(CSV_FILES["mono"], sample=sample)
    df_mono.columns = ["stitch", "se_cui", "se_name"]
    for _, row in df_mono[["se_cui", "se_name"]].drop_duplicates().iterrows():
        if row["se_cui"] not in effects:
            effects[row["se_cui"]] = (row["se_name"], None)

    logger.info("  Total de efeitos únicos: %d", len(effects))

    data = [
        {"umls_cui": cui, "name": name, "category": cat}
        for cui, (name, cat) in effects.items()
    ]

    cypher = """
        UNWIND $rows AS row
        MERGE (s:SideEffect {umls_cui: row.umls_cui})
        ON CREATE SET s.name = row.name, s.category = row.category
    """
    run_in_batches(driver, data, cypher, label="SideEffect")


# ==============================================================================
# Etapas de carga — Arestas
# ==============================================================================

def load_targets_edges(driver, sample=None):
    """
    Cria arestas (:Drug)-[:TARGETS]->(:Protein).
    Fonte: bio-decagon-targets.csv
    """
    logger.info("=" * 60)
    logger.info("ETAPA 4: Criando arestas :TARGETS")
    logger.info("=" * 60)

    df = read_csv(CSV_FILES["targets"], sample=sample)
    df.columns = ["stitch", "gene"]
    df["gene"] = df["gene"].astype(int)

    data = [
        {"stitch_id": row["stitch"], "gene_id": row["gene"]}
        for _, row in df.iterrows()
    ]

    cypher = """
        UNWIND $rows AS row
        MATCH (d:Drug {stitch_id: row.stitch_id})
        MATCH (p:Protein {gene_id: row.gene_id})
        MERGE (d)-[:TARGETS]->(p)
    """
    run_in_batches(driver, data, cypher, label="TARGETS")


def load_ppi_edges(driver, sample=None):
    """
    Cria arestas (:Protein)-[:INTERACTS_WITH]->(:Protein).
    Fonte: bio-decagon-ppi.csv
    """
    logger.info("=" * 60)
    logger.info("ETAPA 5: Criando arestas :INTERACTS_WITH")
    logger.info("=" * 60)

    df = read_csv(CSV_FILES["ppi"], sample=sample)
    df.columns = ["gene_1", "gene_2"]
    df["gene_1"] = df["gene_1"].astype(int)
    df["gene_2"] = df["gene_2"].astype(int)

    data = [
        {"gene_1": row["gene_1"], "gene_2": row["gene_2"]}
        for _, row in df.iterrows()
    ]

    cypher = """
        UNWIND $rows AS row
        MATCH (p1:Protein {gene_id: row.gene_1})
        MATCH (p2:Protein {gene_id: row.gene_2})
        MERGE (p1)-[:INTERACTS_WITH]->(p2)
    """
    run_in_batches(driver, data, cypher, label="INTERACTS_WITH")


def load_mono_effect_edges(driver, sample=None):
    """
    Cria arestas (:Drug)-[:HAS_MONO_EFFECT]->(:SideEffect).
    Fonte: bio-decagon-mono.csv
    """
    logger.info("=" * 60)
    logger.info("ETAPA 6: Criando arestas :HAS_MONO_EFFECT")
    logger.info("=" * 60)

    df = read_csv(CSV_FILES["mono"], sample=sample)
    df.columns = ["stitch", "se_cui", "se_name"]

    data = [
        {"stitch_id": row["stitch"], "umls_cui": row["se_cui"]}
        for _, row in df.iterrows()
    ]

    cypher = """
        UNWIND $rows AS row
        MATCH (d:Drug {stitch_id: row.stitch_id})
        MATCH (s:SideEffect {umls_cui: row.umls_cui})
        MERGE (d)-[:HAS_MONO_EFFECT]->(s)
    """
    run_in_batches(driver, data, cypher, label="HAS_MONO_EFFECT")


def load_combo_effect_edges(driver, sample=None):
    """
    Cria arestas (:Drug)-[:CAUSES_COMBINED {se_id, se_name}]->(:Drug).
    Fonte: bio-decagon-combo.csv (~4.65M linhas)
    Processado em chunks para economizar memória.
    """
    logger.info("=" * 60)
    logger.info("ETAPA 7: Criando arestas :CAUSES_COMBINED")
    logger.info("=" * 60)

    csv_path = CSV_FILES["combo"]
    if not csv_path.exists():
        logger.error("Arquivo não encontrado: %s", csv_path)
        return

    chunk_size = 100_000
    total_processed = 0
    chunk_num = 0
    rows_read = 0

    logger.info("  Processando em chunks de %d linhas...", chunk_size)

    cypher = """
        UNWIND $rows AS row
        MATCH (d1:Drug {stitch_id: row.stitch_1})
        MATCH (d2:Drug {stitch_id: row.stitch_2})
        MERGE (d1)-[:CAUSES_COMBINED {se_id: row.se_cui, se_name: row.se_name}]->(d2)
    """

    for chunk in pd.read_csv(csv_path, dtype=str, chunksize=chunk_size):
        chunk.columns = ["stitch_1", "stitch_2", "se_cui", "se_name"]
        chunk_num += 1
        rows_read += len(chunk)

        # Se --sample foi definido e já lemos o suficiente, parar
        if sample and rows_read > sample:
            chunk = chunk.head(sample - (rows_read - len(chunk)))
            if len(chunk) == 0:
                break

        data = [
            {
                "stitch_1": row["stitch_1"],
                "stitch_2": row["stitch_2"],
                "se_cui": row["se_cui"],
                "se_name": row["se_name"],
            }
            for _, row in chunk.iterrows()
        ]

        # Processar este chunk em sub-batches de BATCH_SIZE
        with driver.session() as session:
            for i in range(0, len(data), BATCH_SIZE):
                batch = data[i : i + BATCH_SIZE]

                def _write_tx(tx, rows):
                    tx.run(cypher, rows=rows)

                session.execute_write(_write_tx, batch)

        total_processed += len(data)
        logger.info("  Chunk %d: %d linhas processadas (total: %d)",
                    chunk_num, len(data), total_processed)

        if sample and rows_read >= sample:
            break

    logger.info("  ✓ %d arestas CAUSES_COMBINED processadas", total_processed)


# ==============================================================================
# Resumo de contagens
# ==============================================================================
def print_summary(driver):
    """Imprime contagens de nós e arestas no grafo."""
    logger.info("")
    logger.info("Resumo de contagens Neo4j:")

    with driver.session() as session:
        # Nós
        for label in ["Drug", "Protein", "SideEffect"]:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
            count = result.single()["c"]
            logger.info("  %-30s %10d nós", f":{label}", count)

        # Arestas
        for rel_type in ["TARGETS", "INTERACTS_WITH", "CAUSES_COMBINED", "HAS_MONO_EFFECT"]:
            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS c")
            count = result.single()["c"]
            logger.info("  %-30s %10d arestas", f":{rel_type}", count)


# ==============================================================================
# Main
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Carrega os datasets DECAGON no Neo4j.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python load_graph.py                    # carga completa
  python load_graph.py --sample 1000      # amostra de 1000 linhas
  python load_graph.py --skip-combo       # pula CAUSES_COMBINED (4.65M arestas)
  python load_graph.py --no-constraints   # pula criação de constraints
        """
    )
    parser.add_argument(
        "--sample", "-s",
        type=int,
        default=None,
        help="Número máximo de linhas a carregar de cada CSV (para testes)."
    )
    parser.add_argument(
        "--skip-combo",
        action="store_true",
        help="Pula o carregamento do CAUSES_COMBINED (útil para testes rápidos)."
    )
    parser.add_argument(
        "--no-constraints",
        action="store_true",
        help="Não cria constraints (assume que já existem)."
    )

    args = parser.parse_args()

    if args.sample:
        logger.info("Modo amostra: limitado a %d linhas por CSV", args.sample)

    start = time.time()

    driver = None
    try:
        driver = get_driver()

        # 0. Constraints
        if not args.no_constraints:
            create_constraints(driver)

        # 1-3. Nós
        load_drug_nodes(driver, sample=args.sample)
        load_protein_nodes(driver, sample=args.sample)
        load_side_effect_nodes(driver, sample=args.sample)

        # 4-7. Arestas
        load_targets_edges(driver, sample=args.sample)
        load_ppi_edges(driver, sample=args.sample)
        load_mono_effect_edges(driver, sample=args.sample)

        if not args.skip_combo:
            load_combo_effect_edges(driver, sample=args.sample)
        else:
            logger.info("Combo pulado (--skip-combo)")

        elapsed = time.time() - start
        logger.info("")
        logger.info("=" * 60)
        logger.info("Carga concluída em %.1f segundos (%.1f minutos)",
                    elapsed, elapsed / 60)
        logger.info("=" * 60)

        # Resumo
        print_summary(driver)

    except Exception as e:
        logger.error("Erro: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        if driver:
            driver.close()
            logger.info("Conexão Neo4j encerrada.")


if __name__ == "__main__":
    main()
