"""
Loader de queries SQL — lê ficheiros .sql de sql/queries/ e executa-os.

Nenhuma query SQL é escrita inline neste módulo. Todas vivem nos ficheiros
.sql versionados no repositório.
"""
from pathlib import Path

import pandas as pd

from app.backend.connections.postgres import get_pg_connection

# Pasta de queries SQL: app/backend/queries/ → ../../../sql/queries/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SQL_DIR = PROJECT_ROOT / "sql" / "queries"


def load_sql(filename: str) -> str:
    """Lê o conteúdo de um ficheiro .sql e retorna como string."""
    path = SQL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Query SQL não encontrada: {path}")
    return path.read_text(encoding="utf-8")


def run_sql(filename: str, params: dict | None = None) -> pd.DataFrame:
    """
    Lê um ficheiro .sql, executa-o no PostgreSQL e retorna um DataFrame.

    Os parâmetros são passados via dict do psycopg2 (ex: %(drug_a_id)s).
    """
    query = load_sql(filename)
    conn = get_pg_connection()
    with conn.cursor() as cur:
        cur.execute(query, params)
        if cur.description is None:
            return pd.DataFrame()
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)
