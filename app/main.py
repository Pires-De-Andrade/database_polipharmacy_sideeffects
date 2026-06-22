"""
Ponto de entrada da aplicação Streamlit — Sistema de Consulta de Risco Farmacológico.

Execução:
    cd <raiz do projecto>
    streamlit run app/main.py
"""
import sys
from pathlib import Path

# Garantir que a raiz do projecto está no sys.path para imports "app.*"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.layout import inject_css, render_header
from app.frontend.components.selector import render_selector
from app.frontend.components.risk_profile import render_risk_profile
from app.frontend.components.molecular_graph import render_molecular_graph
from app.frontend.components.paradigm_compare import render_paradigm_compare
from app.backend.analysis import analyze_drug_pair
from app.backend.connections.postgres import pg_status
from app.backend.connections.neo4j_db import neo4j_status


# ── Configuração da página ────────────────────────────────────────────────
st.set_page_config(
    page_title="Consulta de Risco Farmacológico",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Estilos e Header ──────────────────────────────────────────────────────
inject_css()
render_header()

# ── Status de conexão (sidebar) ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### Conexões")

    pg_ok, pg_detail = pg_status()
    if pg_ok:
        st.markdown(f'<span class="conn-status conn-ok">✓ PostgreSQL</span> {pg_detail}',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="conn-status conn-err">✗ PostgreSQL</span> {pg_detail}',
                    unsafe_allow_html=True)

    n4_ok, n4_detail = neo4j_status()
    if n4_ok:
        st.markdown(f'<span class="conn-status conn-ok">✓ Neo4j</span> {n4_detail}',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="conn-status conn-err">✗ Neo4j</span> {n4_detail}',
                    unsafe_allow_html=True)

    st.divider()
    st.caption("Dados: DECAGON / SNAP Stanford")
    st.caption("Projecto académico — Bases de Dados 2025")

if not pg_ok:
    st.error("Não foi possível conectar ao PostgreSQL.")
    st.info(
        "Crie um arquivo `.env` na raiz do projeto com `PG_HOST`, `PG_PORT`, "
        "`PG_DBNAME`, `PG_USER` e `PG_PASSWORD` corretos. Sem essa conexão, "
        "a lista de medicamentos não pode ser carregada."
    )
    st.stop()

# ── Selecção de medicamentos ──────────────────────────────────────────────
drug_a_id, drug_b_id, should_analyze = render_selector()

# ── Análise ───────────────────────────────────────────────────────────────
if should_analyze and drug_a_id is not None and drug_b_id is not None:
    with st.spinner("Analisando combinação nos dois paradigmas…"):
        result = analyze_drug_pair(drug_a_id, drug_b_id)

    if not result["found"]:
        st.markdown(
            '<div class="not-found-panel">'
            "Combinação não encontrada nos dados observacionais."
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        # ── Tabs ──────────────────────────────────────────────────────
        tab1, tab2, tab3 = st.tabs([
            "📊 Perfil de Risco",
            "🧬 Contexto Molecular",
            "⚖️ Comparação de Paradigmas",
        ])

        with tab1:
            render_risk_profile(result)

        with tab2:
            render_molecular_graph(result)

        with tab3:
            render_paradigm_compare(result)
