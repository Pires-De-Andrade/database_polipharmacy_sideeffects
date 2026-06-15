#!/usr/bin/env python3
"""
==============================================================================
Projeto BD Polifarmácia — Validação de Carga
==============================================================================
Verifica se a carga nos bancos PostgreSQL e Neo4j foi concluída corretamente.

Uso:
    python validate.py

Variáveis de ambiente (.env):
    PG_HOST, PG_PORT, PG_DBNAME, PG_USER, PG_PASSWORD
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

Saída:
    Tabela de contagens + query de amostra em cada banco.
    Código de saída 0 = sucesso, 1 = falha.

Dependências:
    pip install -r requirements.txt
==============================================================================
"""

import os
import sys
from pathlib import Path

import psycopg2
from neo4j import GraphDatabase
from dotenv import load_dotenv

# ==============================================================================
# Configuração
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Largura das colunas na saída
COL_LABEL = 32
COL_COUNT = 12


# ==============================================================================
# Conexões
# ==============================================================================
def get_pg_connection():
    """Cria conexão com o PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
        dbname=os.getenv("PG_DBNAME", "polifarmacia"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "postgres"),
    )


def get_neo4j_driver():
    """Cria driver Neo4j."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


# ==============================================================================
# Validação PostgreSQL
# ==============================================================================
def validate_postgresql():
    """Valida contagens e executa query de amostra no PostgreSQL."""
    print("=" * 56)
    print("[PostgreSQL]")
    print("=" * 56)

    tables = [
        "drug",
        "protein",
        "side_effect",
        "drug_protein_target",
        "protein_interaction",
        "drug_mono_effect",
        "drug_combination_effect",
    ]

    has_zero = False

    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        # Contagens
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
            count = cur.fetchone()[0]
            status = "" if count > 0 else "  ← VAZIO!"
            print(f"  {table:<{COL_LABEL}} : {count:>{COL_COUNT},} registros{status}")
            if count == 0:
                has_zero = True

        # Query de amostra: top 5 drogas por efeitos combinados
        print()
        print("  Query de amostra (top 5 drogas por efeitos combinados):")
        print("  " + "-" * 52)

        cur.execute("""
            SELECT d.stitch_id, COUNT(*) AS n_effects
            FROM drug d
            JOIN drug_combination_effect dce ON d.drug_id = dce.drug_a_id
            GROUP BY d.stitch_id
            ORDER BY n_effects DESC
            LIMIT 5
        """)
        rows = cur.fetchall()
        if rows:
            print(f"  {'stitch_id':<20} {'n_effects':>10}")
            print("  " + "-" * 32)
            for row in rows:
                print(f"  {row[0]:<20} {row[1]:>10,}")
        else:
            print("  (nenhum resultado)")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"\n  ERRO ao conectar no PostgreSQL: {e}")
        return False

    return not has_zero


# ==============================================================================
# Validação Neo4j
# ==============================================================================
def validate_neo4j():
    """Valida contagens e executa query de amostra no Neo4j."""
    print()
    print("=" * 56)
    print("[Neo4j]")
    print("=" * 56)

    node_labels = ["Drug", "Protein", "SideEffect"]
    rel_types = ["TARGETS", "INTERACTS_WITH", "CAUSES_COMBINED", "HAS_MONO_EFFECT"]

    has_zero = False

    try:
        driver = get_neo4j_driver()

        with driver.session() as session:
            # Contagem de nós
            for label in node_labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
                count = result.single()["c"]
                status = "" if count > 0 else "  ← VAZIO!"
                print(f"  :{label:<{COL_LABEL - 1}} : {count:>{COL_COUNT},} nós{status}")
                if count == 0:
                    has_zero = True

            # Contagem de arestas
            for rel in rel_types:
                result = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c")
                count = result.single()["c"]
                status = "" if count > 0 else "  ← VAZIO!"
                print(f"  :{rel:<{COL_LABEL - 1}} : {count:>{COL_COUNT},} arestas{status}")
                if count == 0:
                    has_zero = True

            # Query de amostra: 5 drogas com mais arestas TARGETS
            print()
            print("  Query de amostra (top 5 drogas por alvos proteicos):")
            print("  " + "-" * 52)

            result = session.run("""
                MATCH (d:Drug)-[r:TARGETS]->(p:Protein)
                WITH d.stitch_id AS drug, COUNT(p) AS n_targets
                RETURN drug, n_targets
                ORDER BY n_targets DESC
                LIMIT 5
            """)
            records = list(result)
            if records:
                print(f"  {'stitch_id':<20} {'n_targets':>10}")
                print("  " + "-" * 32)
                for record in records:
                    print(f"  {record['drug']:<20} {record['n_targets']:>10,}")
            else:
                print("  (nenhum resultado)")

        driver.close()

    except Exception as e:
        print(f"\n  ERRO ao conectar no Neo4j: {e}")
        return False

    return not has_zero


# ==============================================================================
# Main
# ==============================================================================
def main():
    print()
    print("  Validação de Carga — Projeto BD Polifarmácia")
    print()

    pg_ok = validate_postgresql()
    neo4j_ok = validate_neo4j()

    print()
    print("=" * 56)

    if pg_ok and neo4j_ok:
        print("  Validação concluída com sucesso")
        print("=" * 56)
        sys.exit(0)
    else:
        problems = []
        if not pg_ok:
            problems.append("PostgreSQL")
        if not neo4j_ok:
            problems.append("Neo4j")
        print(f"  FALHA na validação: {', '.join(problems)} com tabelas vazias ou erros")
        print("=" * 56)
        sys.exit(1)


if __name__ == "__main__":
    main()
