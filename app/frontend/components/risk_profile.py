"""
Tab 1 — Perfil de Risco (PostgreSQL).

Exibe métricas agregadas, tabela de efeitos da combinação e painéis
de efeitos mono (baseline) de cada medicamento.
"""
import streamlit as st
import pandas as pd

from app.frontend.layout import render_query_footer


def render_risk_profile(data: dict):
    """Renderiza a Tab 1 com os resultados do PostgreSQL."""
    df: pd.DataFrame = data["combination_effects"]

    if df.empty:
        st.markdown(
            '<div class="not-found-panel">'
            "Combinação não encontrada nos dados observacionais do PostgreSQL."
            "</div>",
            unsafe_allow_html=True,
        )
        render_query_footer("PostgreSQL", data["sql_time_ms"])
        return

    # ── Métricas no topo ──────────────────────────────────────────────────
    total_effects = len(df)

    # Categoria mais frequente
    if "category" in df.columns and df["category"].notna().any():
        top_category = df["category"].value_counts().idxmax()
        top_category_count = int(df["category"].value_counts().iloc[0])
    else:
        top_category = "N/D"
        top_category_count = 0

    # Distribuição de categorias para indicador de diversidade
    n_categories = df["category"].nunique() if "category" in df.columns else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Efeitos Colaterais", total_effects)
    with col2:
        st.metric("Categoria Mais Frequente", top_category, f"{top_category_count} efeitos")
    with col3:
        st.metric("Categorias Distintas", n_categories)

    # ── Tabela principal ──────────────────────────────────────────────────
    st.markdown("##### Efeitos Colaterais da Combinação")

    display_df = df.rename(columns={
        "side_effect_name": "Efeito Colateral",
        "category": "Categoria",
        "umls_cui": "Código UMLS",
    })

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=min(400, 35 * len(display_df) + 38),
    )

    # ── Efeitos Mono (Baseline) ───────────────────────────────────────────
    st.markdown("##### Efeitos Individuais — Baseline de Risco")
    st.markdown(
        '<div class="interpretation-panel">'
        "Efeitos observados em uso individual — referência antes da combinação."
        "</div>",
        unsafe_allow_html=True,
    )

    mono_a: pd.DataFrame = data["mono_a"]
    mono_b: pd.DataFrame = data["mono_b"]

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"**Medicamento A** — {len(mono_a)} efeitos individuais")
        if mono_a.empty:
            st.info("Sem efeitos mono registados para este medicamento.")
        else:
            st.dataframe(
                mono_a.rename(columns={
                    "side_effect_name": "Efeito",
                    "category": "Categoria",
                    "umls_cui": "UMLS",
                }),
                use_container_width=True,
                hide_index=True,
                height=250,
            )

    with col_b:
        st.markdown(f"**Medicamento B** — {len(mono_b)} efeitos individuais")
        if mono_b.empty:
            st.info("Sem efeitos mono registados para este medicamento.")
        else:
            st.dataframe(
                mono_b.rename(columns={
                    "side_effect_name": "Efeito",
                    "category": "Categoria",
                    "umls_cui": "UMLS",
                }),
                use_container_width=True,
                hide_index=True,
                height=250,
            )

    # ── Rodapé ────────────────────────────────────────────────────────────
    render_query_footer("PostgreSQL", data["sql_time_ms"])
