"""
Projeto BD Polifarmácia — App de demonstração (Streamlit)
=========================================================
Entrypoint. Mostra a visão geral do projeto e o status das conexões com os
bancos PostgreSQL e Neo4j (hospedados na GCP).

Execução:
    streamlit run app/Home.py
"""
import streamlit as st

from backend.db import neo4j_status, pg_status

st.set_page_config(
    page_title="Polifarmácia — Demo BD",
    page_icon="💊",
    layout="wide",
)

st.title("💊 Polifarmácia — Efeitos Colaterais de Combinações de Medicamentos")
st.caption(
    "Demonstração dual-paradigma (PostgreSQL × Neo4j) sobre os datasets DECAGON "
    "(Zitnik et al., 2018). Bancos hospedados na GCP."
)

# ──────────────────────────────────────────────────────────────────────────────
# Status das conexões
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("Status das conexões")
col_pg, col_neo = st.columns(2)

with col_pg:
    pg = pg_status()
    if pg.ok:
        st.success("🐘 **PostgreSQL** conectado")
        st.caption(pg.detail)
    else:
        st.error("🐘 **PostgreSQL** indisponível")
        st.caption(pg.detail)

with col_neo:
    neo = neo4j_status()
    if neo.ok:
        st.success("🕸️ **Neo4j** conectado")
        st.caption(neo.detail)
    else:
        st.error("🕸️ **Neo4j** indisponível")
        st.caption(neo.detail)

if not (pg.ok and neo.ok):
    st.warning(
        "Algum banco não respondeu. Verifique o arquivo `.env` na raiz do projeto "
        "(use `app/.env.example` como modelo) e se as instâncias GCP estão ativas e "
        "acessíveis a partir desta máquina (IP autorizado / SSL)."
    )

st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# Visão geral
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("Sobre o projeto")
st.markdown(
    """
O projeto modela **efeitos colaterais de polifarmácia** — os efeitos adversos
que surgem quando **dois medicamentos são usados em conjunto** — em **dois
paradigmas de banco de dados**, para comparar suas forças:

| | PostgreSQL (relacional) | Neo4j (grafo) |
|---|---|---|
| **Modela** | tabelas + chaves estrangeiras | nós + arestas |
| **Brilha em** | agregação em massa (`GROUP BY`), conjuntos | travessia de rede, caminhos, vizinhança |

Use o menu lateral para navegar:

- **⚖️ Comparação Dual-Paradigma** — a mesma pergunta resolvida em SQL e Cypher, lado a lado.
- **🔬 Explorador Analítico** — as consultas do projeto (hub drugs, pares perigosos, efeitos emergentes, perfil de risco de droga…).
- **🕸️ Visualização de Grafo** — subgrafos interativos, proteínas compartilhadas e caminho mais curto entre drogas.
"""
)

st.divider()
st.caption(
    "Baseado em Zitnik, Agrawal & Leskovec (2018), *Modeling polypharmacy side "
    "effects with graph convolutional networks*, Bioinformatics 34(13). "
    "Datasets: DECAGON / SNAP Stanford."
)
