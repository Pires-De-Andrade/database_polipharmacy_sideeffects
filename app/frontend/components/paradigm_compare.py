"""
Tab 3 — Comparação de Paradigmas.

Exibe as queries reais lado a lado, gráfico de barras comparativo
dos tempos de execução, e painel conclusivo sobre complementaridade.
"""
import streamlit as st
import plotly.graph_objects as go

from app.frontend.layout import render_query_footer


def render_paradigm_compare(data: dict):
    """Renderiza a Tab 3 com a comparação entre SQL e Cypher."""

    # ── Queries reais lado a lado ─────────────────────────────────────────
    st.markdown("##### Queries Executadas")

    col_sql, col_cypher = st.columns(2)

    with col_sql:
        st.markdown("**PostgreSQL — Consulta Estruturada**")
        st.code(data["sql_query_text"], language="sql")
        st.caption("Optimizado para: filtragem, agregação, relatórios tabulares")

    with col_cypher:
        st.markdown("**Neo4j — Travessia de Grafo**")
        st.code(data["cypher_query_text"], language="cypher")
        st.caption("Optimizado para: relações, caminhos, vizinhança molecular")

    # ── Gráfico de barras comparativo ─────────────────────────────────────
    st.markdown("##### Tempo de Execução")

    sql_ms = data["sql_time_ms"]
    cypher_ms = data["cypher_time_ms"]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=["PostgreSQL"],
        x=[sql_ms],
        orientation="h",
        marker_color="#1B3A5C",
        text=[f"{sql_ms:.1f}ms"],
        textposition="outside",
        name="PostgreSQL",
    ))

    fig.add_trace(go.Bar(
        y=["Neo4j"],
        x=[cypher_ms],
        orientation="h",
        marker_color="#E67E22",
        text=[f"{cypher_ms:.1f}ms"],
        textposition="outside",
        name="Neo4j",
    ))

    max_val = max(sql_ms, cypher_ms, 1)
    fig.update_layout(
        xaxis_title="Tempo (ms)",
        xaxis=dict(range=[0, max_val * 1.3]),
        yaxis=dict(autorange="reversed"),
        height=180,
        margin=dict(l=10, r=30, t=10, b=40),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Painel conclusivo ─────────────────────────────────────────────────
    st.markdown("##### Conclusão")
    st.markdown(
        '<div class="interpretation-panel">'
        "O <strong>modelo relacional</strong> respondeu: quais efeitos foram observados "
        "e com que frequência foram reportados.<br><br>"
        "O <strong>modelo de grafos</strong> respondeu: por que estes medicamentos "
        "interagem a nível molecular.<br><br>"
        "As duas perguntas são complementares — <strong>nenhum paradigma substitui "
        "o outro</strong>."
        "</div>",
        unsafe_allow_html=True,
    )
