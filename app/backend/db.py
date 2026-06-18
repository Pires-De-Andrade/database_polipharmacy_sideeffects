"""
Camada de conexão com os bancos de dados (PostgreSQL + Neo4j).

As conexões são cacheadas com `st.cache_resource` para que sejam criadas uma
única vez por sessão do Streamlit (evita reabrir socket a cada interação).
Tanto o PostgreSQL quanto o Neo4j são hospedados separadamente na GCP.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import psycopg2
import streamlit as st
from neo4j import GraphDatabase

from backend.config import neo4j_config, pg_config


@dataclass
class ConnStatus:
    """Resultado de uma tentativa de conexão, para exibir no painel de status."""
    ok: bool
    detail: str


# ──────────────────────────────────────────────────────────────────────────────
# PostgreSQL
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Conectando ao PostgreSQL…")
def get_pg_connection():
    """Abre (e cacheia) a conexão com o PostgreSQL na GCP."""
    cfg = pg_config()
    conn = psycopg2.connect(
        host=cfg["host"],
        port=cfg["port"],
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
        sslmode=cfg["sslmode"],
        connect_timeout=10,
    )
    conn.autocommit = True  # apenas leitura na app; evita transações pendentes
    return conn


def pg_status() -> ConnStatus:
    """Verifica se o PostgreSQL responde, sem propagar exceção."""
    try:
        conn = get_pg_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
        cfg = pg_config()
        return ConnStatus(True, f"{cfg['host']}:{cfg['port']}/{cfg['dbname']} — {version.split(',')[0]}")
    except Exception as e:  # noqa: BLE001 — queremos reportar qualquer falha na UI
        # Invalida o recurso cacheado para permitir nova tentativa após corrigir o .env
        get_pg_connection.clear()
        return ConnStatus(False, str(e))


def run_sql(query: str, params: tuple | None = None) -> pd.DataFrame:
    """Executa uma query SQL de leitura e retorna um DataFrame."""
    conn = get_pg_connection()
    with conn.cursor() as cur:
        cur.execute(query, params)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)


# ──────────────────────────────────────────────────────────────────────────────
# Neo4j
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Conectando ao Neo4j…")
def get_neo4j_driver():
    """Cria (e cacheia) o driver Neo4j apontando para a instância na GCP."""
    cfg = neo4j_config()
    driver = GraphDatabase.driver(
        cfg["uri"],
        auth=(cfg["user"], cfg["password"]),
        connection_timeout=10,
    )
    return driver


def neo4j_status() -> ConnStatus:
    """Verifica se o Neo4j responde, sem propagar exceção."""
    try:
        driver = get_neo4j_driver()
        driver.verify_connectivity()
        cfg = neo4j_config()
        return ConnStatus(True, f"{cfg['uri']} (db: {cfg['database']})")
    except Exception as e:  # noqa: BLE001
        get_neo4j_driver.clear()
        return ConnStatus(False, str(e))


def run_cypher(query: str, params: dict | None = None) -> pd.DataFrame:
    """Executa uma query Cypher e retorna um DataFrame."""
    cfg = neo4j_config()
    driver = get_neo4j_driver()
    with driver.session(database=cfg["database"]) as session:
        result = session.run(query, **(params or {}))
        records = [r.data() for r in result]
    return pd.DataFrame(records)
