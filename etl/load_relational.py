#!/usr/bin/env python3
"""
==============================================================================
Projeto BD Polifarmácia — ETL: Carga dos CSVs no PostgreSQL
==============================================================================
Carrega os datasets do DECAGON (SNAP Stanford) no banco relacional PostgreSQL.

Uso:
    python load_relational.py                      # carga completa
    python load_relational.py --sample 1000        # apenas primeiras 1000 linhas/CSV
    python load_relational.py --skip-combo         # pula o combo (4.65M linhas)

Variáveis de ambiente (.env):
    PG_HOST     (default: localhost)
    PG_PORT     (default: 5432)
    PG_DBNAME   (default: polifarmacia)
    PG_USER     (default: postgres)
    PG_PASSWORD (default: postgres)

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
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

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

# Tamanho do batch para execute_values (rows por INSERT)
BATCH_SIZE = 5000


# ==============================================================================
# Conexão com PostgreSQL
# ==============================================================================
def get_connection():
    """Cria conexão com o PostgreSQL usando variáveis de ambiente."""
    load_dotenv(BASE_DIR / ".env")

    params = {
        "host":     os.getenv("PG_HOST", "localhost"),
        "port":     os.getenv("PG_PORT", "5432"),
        "dbname":   os.getenv("PG_DBNAME", "polifarmacia"),
        "user":     os.getenv("PG_USER", "postgres"),
        "password": os.getenv("PG_PASSWORD", "postgres"),
    }
    logger.info("Conectando ao PostgreSQL %s@%s:%s/%s",
                params["user"], params["host"], params["port"], params["dbname"])

    conn = psycopg2.connect(**params)
    conn.autocommit = False
    return conn


# ==============================================================================
# Helpers de inserção em batch
# ==============================================================================
def batch_insert(cur, sql, data, page_size=BATCH_SIZE, label=""):
    """Insere dados em batches usando execute_values para performance."""
    total = len(data)
    inserted = 0

    for i in range(0, total, page_size):
        batch = data[i : i + page_size]
        execute_values(cur, sql, batch, page_size=page_size)
        inserted += len(batch)
        if inserted % (page_size * 10) == 0 or inserted == total:
            logger.info("  [%s] %d / %d (%.1f%%)", label, inserted, total,
                        100 * inserted / total)

    return inserted


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


# ==============================================================================
# Etapas de carga
# ==============================================================================

def load_side_effects(cur, sample=None):
    """
    Carrega side_effect a partir de effectcategories.csv e dos nomes
    encontrados em combo.csv e mono.csv.

    Estratégia:
      1. effectcategories.csv fornece (umls_cui, name, category) para 964 efeitos
      2. combo.csv e mono.csv podem conter efeitos NÃO listados em categories
         → inserimos esses com category = NULL
    """
    logger.info("=" * 60)
    logger.info("ETAPA 1: Carregando side_effect")
    logger.info("=" * 60)

    # 1a. Efeitos com categoria
    df_cat = read_csv(CSV_FILES["categories"], sample=sample)
    df_cat.columns = ["umls_cui", "name", "category"]

    # Mapa completo de efeitos: umls_cui -> (name, category)
    effects = {}
    for _, row in df_cat.iterrows():
        effects[row["umls_cui"]] = (row["name"], row["category"])

    # 1b. Efeitos do combo (podem ter novos)
    df_combo = read_csv(CSV_FILES["combo"], sample=sample)
    df_combo.columns = ["stitch_1", "stitch_2", "se_cui", "se_name"]
    for _, row in df_combo[["se_cui", "se_name"]].drop_duplicates().iterrows():
        if row["se_cui"] not in effects:
            effects[row["se_cui"]] = (row["se_name"], None)

    # 1c. Efeitos do mono (podem ter novos)
    df_mono = read_csv(CSV_FILES["mono"], sample=sample)
    df_mono.columns = ["stitch", "se_cui", "se_name"]
    for _, row in df_mono[["se_cui", "se_name"]].drop_duplicates().iterrows():
        if row["se_cui"] not in effects:
            effects[row["se_cui"]] = (row["se_name"], None)

    # Inserir
    data = [(cui, name, cat) for cui, (name, cat) in effects.items()]
    sql = """
        INSERT INTO side_effect (umls_cui, name, category)
        VALUES %s
        ON CONFLICT (umls_cui) DO NOTHING
    """
    count = batch_insert(cur, sql, data, label="side_effect")
    logger.info("  ✓ %d efeitos colaterais inseridos", count)

    return effects


def load_drugs(cur, sample=None):
    """
    Extrai todos os STITCH IDs únicos dos CSVs de targets, combo e mono,
    e insere na tabela drug.
    """
    logger.info("=" * 60)
    logger.info("ETAPA 2: Carregando drug")
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

    data = [(sid,) for sid in sorted(stitch_ids)]
    sql = """
        INSERT INTO drug (stitch_id)
        VALUES %s
        ON CONFLICT (stitch_id) DO NOTHING
    """
    count = batch_insert(cur, sql, data, label="drug")
    logger.info("  ✓ %d drogas inseridas", count)


def load_proteins(cur, sample=None):
    """
    Extrai todos os Gene IDs únicos dos CSVs de PPI e targets,
    e insere na tabela protein.
    """
    logger.info("=" * 60)
    logger.info("ETAPA 3: Carregando protein")
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

    data = [(int(gid),) for gid in sorted(gene_ids)]
    sql = """
        INSERT INTO protein (gene_id)
        VALUES %s
        ON CONFLICT (gene_id) DO NOTHING
    """
    count = batch_insert(cur, sql, data, label="protein")
    logger.info("  ✓ %d proteínas inseridas", count)


def load_drug_protein_targets(cur, sample=None):
    """
    Carrega relações droga → proteína-alvo do bio-decagon-targets.csv.
    Faz lookup dos IDs surrogate via subquery.
    """
    logger.info("=" * 60)
    logger.info("ETAPA 4: Carregando drug_protein_target")
    logger.info("=" * 60)

    df = read_csv(CSV_FILES["targets"], sample=sample)
    df.columns = ["stitch", "gene"]
    df["gene"] = df["gene"].astype(int)

    data = [(row["stitch"], row["gene"]) for _, row in df.iterrows()]

    sql = """
        INSERT INTO drug_protein_target (drug_id, protein_id)
        VALUES %s
        ON CONFLICT (drug_id, protein_id) DO NOTHING
    """
    # Precisamos resolver stitch_id → drug_id e gene_id → protein_id
    # Estratégia: carregar os mapas em memória para maior velocidade
    cur.execute("SELECT stitch_id, drug_id FROM drug")
    drug_map = dict(cur.fetchall())

    cur.execute("SELECT gene_id, protein_id FROM protein")
    protein_map = dict(cur.fetchall())

    resolved = []
    skipped = 0
    for stitch, gene in data:
        d_id = drug_map.get(stitch)
        p_id = protein_map.get(gene)
        if d_id and p_id:
            resolved.append((d_id, p_id))
        else:
            skipped += 1

    if skipped:
        logger.warning("  ⚠ %d relações ignoradas (drug/protein não encontrados)", skipped)

    count = batch_insert(cur, sql, resolved, label="drug_protein_target")
    logger.info("  ✓ %d relações droga→proteína inseridas", count)


def load_protein_interactions(cur, sample=None):
    """
    Carrega a rede PPI do bio-decagon-ppi.csv.
    Aplica a normalização a < b para respeitar a constraint de simetria.
    """
    logger.info("=" * 60)
    logger.info("ETAPA 5: Carregando protein_interaction")
    logger.info("=" * 60)

    df = read_csv(CSV_FILES["ppi"], sample=sample)
    df.columns = ["gene_1", "gene_2"]
    df["gene_1"] = df["gene_1"].astype(int)
    df["gene_2"] = df["gene_2"].astype(int)

    # Mapa gene_id → protein_id
    cur.execute("SELECT gene_id, protein_id FROM protein")
    protein_map = dict(cur.fetchall())

    resolved = []
    skipped = 0
    for _, row in df.iterrows():
        p_a = protein_map.get(row["gene_1"])
        p_b = protein_map.get(row["gene_2"])
        if p_a and p_b and p_a != p_b:
            # Normalizar: a < b
            if p_a > p_b:
                p_a, p_b = p_b, p_a
            resolved.append((p_a, p_b))
        else:
            skipped += 1

    # Remover duplicatas que possam surgir da normalização
    resolved = list(set(resolved))

    if skipped:
        logger.warning("  ⚠ %d interações ignoradas", skipped)

    sql = """
        INSERT INTO protein_interaction (protein_a_id, protein_b_id)
        VALUES %s
        ON CONFLICT (protein_a_id, protein_b_id) DO NOTHING
    """
    count = batch_insert(cur, sql, resolved, label="protein_interaction")
    logger.info("  ✓ %d interações PPI inseridas", count)


def load_drug_mono_effects(cur, sample=None):
    """
    Carrega efeitos colaterais de drogas individuais do bio-decagon-mono.csv.
    """
    logger.info("=" * 60)
    logger.info("ETAPA 6: Carregando drug_mono_effect")
    logger.info("=" * 60)

    df = read_csv(CSV_FILES["mono"], sample=sample)
    df.columns = ["stitch", "se_cui", "se_name"]

    # Mapas de lookup
    cur.execute("SELECT stitch_id, drug_id FROM drug")
    drug_map = dict(cur.fetchall())

    cur.execute("SELECT umls_cui, se_id FROM side_effect")
    se_map = dict(cur.fetchall())

    resolved = []
    skipped = 0
    for _, row in df.iterrows():
        d_id = drug_map.get(row["stitch"])
        s_id = se_map.get(row["se_cui"])
        if d_id and s_id:
            resolved.append((d_id, s_id))
        else:
            skipped += 1

    # Remover duplicatas
    resolved = list(set(resolved))

    if skipped:
        logger.warning("  ⚠ %d efeitos mono ignorados", skipped)

    sql = """
        INSERT INTO drug_mono_effect (drug_id, se_id)
        VALUES %s
        ON CONFLICT (drug_id, se_id) DO NOTHING
    """
    count = batch_insert(cur, sql, resolved, label="drug_mono_effect")
    logger.info("  ✓ %d efeitos mono inseridos", count)


def load_drug_combination_effects(cur, sample=None):
    """
    Carrega efeitos colaterais de pares de drogas do bio-decagon-combo.csv.
    Este é o maior dataset (~4.65M linhas) — processado em chunks.
    Aplica normalização drug_a < drug_b para simetria.
    """
    logger.info("=" * 60)
    logger.info("ETAPA 7: Carregando drug_combination_effect")
    logger.info("=" * 60)

    # Mapas de lookup
    cur.execute("SELECT stitch_id, drug_id FROM drug")
    drug_map = dict(cur.fetchall())

    cur.execute("SELECT umls_cui, se_id FROM side_effect")
    se_map = dict(cur.fetchall())

    sql = """
        INSERT INTO drug_combination_effect (drug_a_id, drug_b_id, se_id)
        VALUES %s
        ON CONFLICT (drug_a_id, drug_b_id, se_id) DO NOTHING
    """

    csv_path = CSV_FILES["combo"]
    if not csv_path.exists():
        logger.error("Arquivo não encontrado: %s", csv_path)
        return

    # Processar em chunks para economizar memória (~4.65M linhas)
    chunk_size = 100_000
    total_inserted = 0
    total_skipped = 0
    chunk_num = 0
    rows_read = 0

    logger.info("  Processando em chunks de %d linhas...", chunk_size)

    for chunk in pd.read_csv(csv_path, dtype=str, chunksize=chunk_size):
        chunk.columns = ["stitch_1", "stitch_2", "se_cui", "se_name"]
        chunk_num += 1
        rows_read += len(chunk)

        # Se --sample foi definido e já lemos o suficiente, parar
        if sample and rows_read > sample:
            chunk = chunk.head(sample - (rows_read - len(chunk)))
            if len(chunk) == 0:
                break

        resolved = []
        skipped = 0

        for _, row in chunk.iterrows():
            d_a = drug_map.get(row["stitch_1"])
            d_b = drug_map.get(row["stitch_2"])
            s_id = se_map.get(row["se_cui"])

            if d_a and d_b and s_id:
                # Normalizar: drug_a < drug_b
                if d_a > d_b:
                    d_a, d_b = d_b, d_a
                resolved.append((d_a, d_b, s_id))
            else:
                skipped += 1

        if resolved:
            execute_values(cur, sql, resolved, page_size=BATCH_SIZE)
            total_inserted += len(resolved)

        total_skipped += skipped
        logger.info("  Chunk %d: %d linhas → %d inseridas, %d ignoradas (total: %d)",
                    chunk_num, len(chunk), len(resolved), skipped, total_inserted)

        if sample and rows_read >= sample:
            break

    if total_skipped:
        logger.warning("  ⚠ %d efeitos combo ignorados no total", total_skipped)

    logger.info("  ✓ %d efeitos de combinação inseridos", total_inserted)


# ==============================================================================
# Execução do schema SQL
# ==============================================================================
def run_schema(cur):
    """Executa os scripts SQL de schema e índices."""
    sql_dir = BASE_DIR / "sql"

    for sql_file in ["schema.sql", "indexes.sql"]:
        path = sql_dir / sql_file
        if path.exists():
            logger.info("Executando %s ...", sql_file)
            cur.execute(path.read_text(encoding="utf-8"))
            logger.info("  ✓ %s executado com sucesso", sql_file)
        else:
            logger.warning("  ⚠ %s não encontrado, pulando", sql_file)


# ==============================================================================
# Main
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Carrega os datasets DECAGON no PostgreSQL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python load_relational.py                   # carga completa
  python load_relational.py --sample 1000     # amostra de 1000 linhas
  python load_relational.py --skip-combo      # pula combo (4.65M linhas)
  python load_relational.py --no-schema       # pula criação do schema
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
        help="Pula o carregamento do combo (útil para testes rápidos)."
    )
    parser.add_argument(
        "--no-schema",
        action="store_true",
        help="Não executa os scripts SQL de schema (assume que já existem)."
    )

    args = parser.parse_args()

    if args.sample:
        logger.info("🔬 Modo amostra: limitado a %d linhas por CSV", args.sample)

    start = time.time()

    try:
        conn = get_connection()
        cur = conn.cursor()

        # 0. Schema
        if not args.no_schema:
            run_schema(cur)
            conn.commit()
            logger.info("Schema criado/atualizado com sucesso.\n")

        # 1. Side Effects (precisa ser primeiro — combo e mono referenciam)
        load_side_effects(cur, sample=args.sample)
        conn.commit()

        # 2. Drugs
        load_drugs(cur, sample=args.sample)
        conn.commit()

        # 3. Proteins
        load_proteins(cur, sample=args.sample)
        conn.commit()

        # 4. Drug → Protein Targets
        load_drug_protein_targets(cur, sample=args.sample)
        conn.commit()

        # 5. PPI
        load_protein_interactions(cur, sample=args.sample)
        conn.commit()

        # 6. Mono effects
        load_drug_mono_effects(cur, sample=args.sample)
        conn.commit()

        # 7. Combo effects
        if not args.skip_combo:
            load_drug_combination_effects(cur, sample=args.sample)
            conn.commit()
        else:
            logger.info("⏭ Combo pulado (--skip-combo)")

        elapsed = time.time() - start
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Carga concluída em %.1f segundos (%.1f minutos)",
                    elapsed, elapsed / 60)
        logger.info("=" * 60)

        # Resumo de contagens
        tables = [
            "drug", "protein", "side_effect",
            "drug_protein_target", "protein_interaction",
            "drug_mono_effect", "drug_combination_effect",
        ]
        logger.info("\nResumo de contagens:")
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
            count = cur.fetchone()[0]
            logger.info("  %-30s %10d linhas", table, count)

    except psycopg2.Error as e:
        logger.error("Erro no PostgreSQL: %s", e)
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error("Arquivo não encontrado: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("Erro inesperado: %s", e, exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
            logger.info("Conexão encerrada.")


if __name__ == "__main__":
    main()
