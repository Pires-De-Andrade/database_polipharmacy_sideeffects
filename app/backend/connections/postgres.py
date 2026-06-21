"""
Conexão com o PostgreSQL — segue o mesmo padrão de etl/load_relational.py.

Lê as credenciais do .env na raiz do projecto (PG_HOST, PG_PORT, PG_DBNAME,
PG_USER, PG_PASSWORD). A conexão é cacheada com @st.cache_resource para
reutilização entre interacções do Streamlit.
"""
import os
from pathlib import Path

import psycopg2
import streamlit as st
from dotenv import load_dotenv

# Raiz do projecto: app/backend/connections/ → ../../../
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _pg_params() -> dict:
    """Parâmetros de conexão PostgreSQL (defaults iguais aos do ETL)."""
    return {
        "host":     os.getenv("PG_HOST", "localhost"),
        "port":     os.getenv("PG_PORT", "5432"),
        "dbname":   os.getenv("PG_DBNAME", "polifarmacia"),
        "user":     os.getenv("PG_USER", "postgres"),
        "password": os.getenv("PG_PASSWORD", "postgres"),
    }


@st.cache_resource(show_spinner="Conectando ao PostgreSQL…")
def get_pg_connection():
    """Abre e cacheia a conexão com o PostgreSQL."""
    params = _pg_params()
    conn = psycopg2.connect(**params)
    conn.autocommit = True  # apenas leitura na app
    return conn


def pg_status() -> tuple[bool, str]:
    """Verifica se o PostgreSQL responde. Retorna (ok, detalhe)."""
    try:
        conn = get_pg_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
        p = _pg_params()
        return True, f"{p['host']}:{p['port']}/{p['dbname']} — {version.split(',')[0]}"
    except Exception as e:
        get_pg_connection.clear()
        return False, str(e)
