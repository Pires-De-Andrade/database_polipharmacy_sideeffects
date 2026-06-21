"""
Componente de selecção de medicamentos (dropdowns + botão).
"""
import streamlit as st
import pandas as pd

from app.backend.queries.sql_loader import run_sql


@st.cache_data(ttl=3600, show_spinner="Carregando lista de medicamentos…")
def _load_drug_list() -> pd.DataFrame:
    """Carrega a lista de medicamentos do PostgreSQL com cache de 1h."""
    return run_sql("streamlit_drug_list.sql")


def render_selector() -> tuple[int | None, int | None, bool]:
    """
    Renderiza os dropdowns de selecção e o botão de análise.

    Retorna:
        (drug_a_id, drug_b_id, should_analyze)
    """
    df_drugs = _load_drug_list()

    if df_drugs.empty:
        st.warning("Nenhum medicamento encontrado na base de dados.")
        return None, None, False

    # Construir opções: label → drug_id
    options = list(df_drugs["label"])
    drug_id_map = dict(zip(df_drugs["label"], df_drugs["drug_id"]))

    col_a, col_b = st.columns(2)

    with col_a:
        label_a = st.selectbox(
            "Medicamento A",
            options=options,
            index=None,
            placeholder="Selecione o primeiro medicamento…",
            key="drug_a",
        )

    # Filtrar opções válidas para Medicamento B com base no Medicamento A
    valid_options_b = options
    if label_a is not None:
        drug_a_id = drug_id_map[label_a]
        try:
            df_valid = run_sql("streamlit_valid_pairs.sql", {"drug_id": drug_a_id})
            if not df_valid.empty:
                valid_ids = set(df_valid["drug_id"])
                valid_options_b = [opt for opt in options if drug_id_map[opt] in valid_ids]
        except Exception:
            pass  # Fallback: mostra todos

    with col_b:
        label_b = st.selectbox(
            "Medicamento B",
            options=valid_options_b,
            index=None,
            placeholder="Selecione o segundo medicamento…",
            key="drug_b",
        )

    # Validação
    both_selected = label_a is not None and label_b is not None
    same_drug = both_selected and label_a == label_b

    if same_drug:
        st.warning("Selecione dois medicamentos **diferentes** para analisar a combinação.")

    # Botão
    can_analyze = both_selected and not same_drug

    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        clicked = st.button(
            "🔍 Analisar Combinação",
            disabled=not can_analyze,
            use_container_width=True,
        )

    if clicked and can_analyze:
        drug_a_id = int(drug_id_map[label_a])
        drug_b_id = int(drug_id_map[label_b])
        return drug_a_id, drug_b_id, True

    return None, None, False
