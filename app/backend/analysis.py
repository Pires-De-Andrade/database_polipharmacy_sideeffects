"""
Orquestrador central de análise.

Recebe um par de drug_ids, executa as queries em ambos os bancos,
mede tempos e retorna um dicionário unificado para o frontend.
"""
from __future__ import annotations

import pandas as pd

from app.backend.queries.sql_loader import load_sql, run_sql
from app.backend.queries.cypher_loader import load_cypher, run_cypher
from app.backend.connections.postgres import get_pg_connection
from app.utils.timer import QueryTimer


def _get_stitch_id(drug_id: int) -> str | None:
    """Resolve drug_id (surrogate) → stitch_id para o driver Neo4j."""
    conn = get_pg_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT stitch_id FROM drug WHERE drug_id = %s", (drug_id,))
        row = cur.fetchone()
    return row[0] if row else None


def analyze_drug_pair(drug_a_id: int, drug_b_id: int) -> dict:
    """
    Executa a análise completa de um par de medicamentos.

    Normaliza a < b para respeitar a constraint do schema.
    Retorna dicionário com todas as chaves esperadas pelo frontend.
    """
    # Normalizar: drug_a_id < drug_b_id (constraint do schema)
    if drug_a_id > drug_b_id:
        drug_a_id, drug_b_id = drug_b_id, drug_a_id

    result = {
        "combination_effects": pd.DataFrame(),
        "mono_a": pd.DataFrame(),
        "mono_b": pd.DataFrame(),
        "graph_data": {},
        "shared_proteins": 0,
        "sql_time_ms": 0.0,
        "cypher_time_ms": 0.0,
        "sql_query_text": "",
        "cypher_query_text": "",
        "found": False,
        "drug_a_id": drug_a_id,
        "drug_b_id": drug_b_id,
    }

    # ── SQL: Carregar texto da query ──────────────────────────────────────
    try:
        result["sql_query_text"] = load_sql("streamlit_combination_risk.sql")
    except FileNotFoundError:
        result["sql_query_text"] = "-- Ficheiro não encontrado"

    # ── SQL: Efeitos da combinação ────────────────────────────────────────
    try:
        params = {"drug_a_id": drug_a_id, "drug_b_id": drug_b_id}
        with QueryTimer() as sql_timer:
            df_combo = run_sql("streamlit_combination_risk.sql", params)
        result["combination_effects"] = df_combo
        result["sql_time_ms"] = sql_timer.elapsed_ms
        result["found"] = len(df_combo) > 0
    except Exception:
        pass  # popular apenas dados disponíveis

    # ── SQL: Efeitos mono de cada medicamento ─────────────────────────────
    try:
        result["mono_a"] = run_sql("streamlit_mono_effects.sql", {"drug_id": drug_a_id})
    except Exception:
        pass

    try:
        result["mono_b"] = run_sql("streamlit_mono_effects.sql", {"drug_id": drug_b_id})
    except Exception:
        pass

    # ── Cypher: Carregar texto da query ───────────────────────────────────
    try:
        result["cypher_query_text"] = load_cypher("streamlit_molecular_context.cypher")
    except FileNotFoundError:
        result["cypher_query_text"] = "// Ficheiro não encontrado"

    # ── Cypher: Contexto molecular ────────────────────────────────────────
    try:
        stitch_a = _get_stitch_id(drug_a_id)
        stitch_b = _get_stitch_id(drug_b_id)

        if stitch_a and stitch_b:
            with QueryTimer() as cypher_timer:
                records = run_cypher(
                    "streamlit_molecular_context.cypher",
                    {"stitch_a": stitch_a, "stitch_b": stitch_b},
                )
            result["cypher_time_ms"] = cypher_timer.elapsed_ms

            if records:
                rec = records[0]
                shared = rec.get("shared_proteins", [])
                excl_a = rec.get("exclusive_a_proteins", [])
                excl_b = rec.get("exclusive_b_proteins", [])
                result["shared_proteins"] = len(shared)
                result["graph_data"] = {
                    "drug_a": {
                        "stitch_id": rec.get("drug_a_stitch", stitch_a),
                        "name": rec.get("drug_a_name", stitch_a),
                    },
                    "drug_b": {
                        "stitch_id": rec.get("drug_b_stitch", stitch_b),
                        "name": rec.get("drug_b_name", stitch_b),
                    },
                    "shared_proteins": shared,
                    "exclusive_a_proteins": excl_a,
                    "exclusive_b_proteins": excl_b,
                }
                # Marcar como found se ao menos um banco retornou dados
                if not result["found"] and (shared or excl_a or excl_b):
                    result["found"] = True
    except Exception:
        pass  # popular apenas dados disponíveis

    return result
