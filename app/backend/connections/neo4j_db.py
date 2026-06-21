"""
Conexão com o Neo4j — segue o mesmo padrão de etl/load_graph.py.

Lê as credenciais do .env na raiz do projecto (NEO4J_URI, NEO4J_USER,
NEO4J_PASSWORD). O driver é cacheado com @st.cache_resource para
reutilização entre interacções do Streamlit.
"""
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Raiz do projecto: app/backend/connections/ → ../../../
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _neo4j_params() -> dict:
    """Parâmetros de conexão Neo4j (defaults iguais aos do ETL)."""
    return {
        "uri":      os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user":     os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "neo4j"),
        "database": os.getenv("NEO4J_DATABASE", "neo4j"),
    }


@st.cache_resource(show_spinner="Conectando ao Neo4j…")
def get_neo4j_driver():
    """Cria e cacheia o driver Neo4j."""
    cfg = _neo4j_params()
    driver = GraphDatabase.driver(
        cfg["uri"],
        auth=(cfg["user"], cfg["password"]),
    )
    return driver


def neo4j_database() -> str:
    """Retorna o nome da database Neo4j configurada."""
    return _neo4j_params()["database"]


def neo4j_status() -> tuple[bool, str]:
    """Verifica se o Neo4j responde. Retorna (ok, detalhe)."""
    try:
        driver = get_neo4j_driver()
        driver.verify_connectivity()
        cfg = _neo4j_params()
        return True, f"{cfg['uri']} (db: {cfg['database']})"
    except Exception as e:
        get_neo4j_driver.clear()
        return False, str(e)
