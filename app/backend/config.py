"""
Configuração central da aplicação Streamlit.

Carrega as variáveis de ambiente do `.env` na raiz do projeto — as MESMAS
usadas pelos scripts de ETL ([etl/load_relational.py], [etl/load_graph.py]),
de modo que não há duplicação de credenciais entre o pipeline e a app.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Raiz do projeto = .../database_polipharmacy_sideeffects (app/backend/ → ../../)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SQL_QUERIES_DIR = PROJECT_ROOT / "sql" / "queries"
CYPHER_QUERIES_DIR = PROJECT_ROOT / "cypher" / "queries"

# Carrega .env da raiz (mesmo arquivo dos ETLs)
load_dotenv(PROJECT_ROOT / ".env")


def pg_config() -> dict:
    """Parâmetros de conexão do PostgreSQL (defaults iguais aos do ETL)."""
    return {
        "host": os.getenv("PG_HOST", "localhost"),
        "port": os.getenv("PG_PORT", "5432"),
        "dbname": os.getenv("PG_DBNAME", "polifarmacia"),
        "user": os.getenv("PG_USER", "postgres"),
        "password": os.getenv("PG_PASSWORD", "postgres"),
        # GCP Cloud SQL normalmente exige SSL; permite override via .env
        "sslmode": os.getenv("PG_SSLMODE", "prefer"),
    }


def neo4j_config() -> dict:
    """Parâmetros de conexão do Neo4j (defaults iguais aos do ETL)."""
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "neo4j"),
        "database": os.getenv("NEO4J_DATABASE", "neo4j"),
    }
