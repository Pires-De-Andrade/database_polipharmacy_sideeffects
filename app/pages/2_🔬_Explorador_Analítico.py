"""
Página: Explorador Analítico.

Expõe as consultas analíticas do projeto como abas navegáveis, com gráficos e
tabelas. Mistura queries PostgreSQL e Neo4j conforme o paradigma mais natural
para cada pergunta.
"""
import streamlit as st

from backend import queries

st.set_page_config(page_title="Explorador Analítico", page_icon="🔬", layout="wide")

st.title("🔬 Explorador Analítico")
st.caption("Consultas analíticas do projeto sobre os datasets DECAGON.")

tabs = st.tabs(
    [
        "💊 Hub Drugs",
        "⚠️ Efeitos mais comuns",
        "🆕 Efeitos emergentes",
        "🔗 Pares perigosos",
        "🗂️ Por categoria",
        "🧬 Hubs de proteína",
        "📋 Perfil de risco",
    ]
)


def _show(loader, msg="Carregando…"):
    """Executa um loader de query e retorna o DataFrame, tratando erros na UI."""
    try:
        with st.spinner(msg):
            return loader()
    except Exception as e:  # noqa: BLE001
        st.error(f"Falha ao consultar o banco: {e}")
        return None


# ── Hub Drugs (SQL) ────────────────────────────────────────────────────────────
with tabs[0]:
    st.subheader("Drogas com mais proteínas-alvo")
    st.caption("Drogas que miram muitas proteínas (hubs farmacológicos) tendem a "
               "interagir com mais fármacos. *Fonte: PostgreSQL.*")
    n = st.slider("Top N", 5, 30, 15, key="hub")
    df = _show(lambda: queries.hub_drugs(n))
    if df is not None and not df.empty:
        st.bar_chart(df.set_index("stitch_id")["n_targets"])
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── Top side effects (SQL) ──────────────────────────────────────────────────────
with tabs[1]:
    st.subheader("Efeitos colaterais mais frequentes em combinações")
    st.caption("Efeitos que aparecem em muitos pares de drogas. *Fonte: PostgreSQL.*")
    c1, c2 = st.columns(2)
    min_pairs = c1.number_input("Mínimo de pares (HAVING)", 0, 5000, 500, step=100)
    lim = c2.slider("Top N", 5, 50, 30, key="tse")
    df = _show(lambda: queries.top_side_effects(min_pairs, lim))
    if df is not None and not df.empty:
        st.bar_chart(df.set_index("side_effect_name")["n_pairs"])
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── Emergent effects (SQL) ──────────────────────────────────────────────────────
with tabs[2]:
    st.subheader("Efeitos emergentes")
    st.caption("O cenário mais perigoso da polifarmácia: efeitos que **não** "
               "ocorrem com nenhuma droga isolada, mas emergem na combinação. "
               "*Fonte: PostgreSQL.*")
    lim = st.slider("Top N", 5, 50, 30, key="emerg")
    df = _show(lambda: queries.emergent_effects(lim))
    if df is not None and not df.empty:
        st.bar_chart(df.set_index("side_effect_name")["n_emergent_pairs"])
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── Dangerous pairs (SQL) ───────────────────────────────────────────────────────
with tabs[3]:
    st.subheader("Pares de drogas mais perigosos")
    st.caption("Pares com mais efeitos colaterais combinados. *Fonte: PostgreSQL.*")
    lim = st.slider("Top N", 5, 50, 20, key="pairs")
    df = _show(lambda: queries.dangerous_pairs(lim))
    if df is not None and not df.empty:
        df = df.assign(par=df["drug_a"] + " + " + df["drug_b"])
        st.bar_chart(df.set_index("par")["n_side_effects"])
        st.dataframe(df.drop(columns="par"), use_container_width=True, hide_index=True)


# ── Category analysis (SQL) ─────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("Distribuição de efeitos por categoria (Disease Class)")
    st.caption("Quais sistemas corporais são mais afetados. *Fonte: PostgreSQL.*")
    df = _show(queries.category_analysis)
    if df is not None and not df.empty:
        st.bar_chart(df.set_index("category")["n_in_combinations"])
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── Protein hubs (Cypher) ───────────────────────────────────────────────────────
with tabs[5]:
    st.subheader("Proteínas hub farmacológicas")
    st.caption("Proteínas com alto grau na rede PPI **e** alvo de várias drogas — "
               "pontos de vulnerabilidade biológica. *Fonte: Neo4j.*")
    c1, c2, c3 = st.columns(3)
    min_ppi = c1.number_input("Grau PPI mínimo", 0, 200, 10)
    min_drugs = c2.number_input("Mín. drogas mirando", 1, 50, 3)
    lim = c3.slider("Top N", 5, 50, 20, key="phub")
    df = _show(lambda: queries.protein_hubs(min_ppi, min_drugs, lim))
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── Drug risk profile (SQL) ─────────────────────────────────────────────────────
with tabs[6]:
    st.subheader("Perfil de risco de uma droga")
    st.caption("Todos os efeitos individuais (MONO) e combinados (COMBO) de uma "
               "droga específica. *Fonte: PostgreSQL.*")
    drugs = _show(lambda: queries.drug_list(2000), "Carregando lista de drogas…")
    if drugs is not None and not drugs.empty:
        options = drugs["stitch_id"].tolist()
        default = "CID000002173" if "CID000002173" in options else options[0]
        stitch = st.selectbox("STITCH ID da droga", options, index=options.index(default))
        if st.button("Gerar perfil", key="profile"):
            df = _show(lambda: queries.drug_risk_profile(stitch))
            if df is not None:
                if df.empty:
                    st.info("Nenhum efeito registrado para esta droga.")
                else:
                    m1, m2 = st.columns(2)
                    m1.metric("Efeitos individuais (MONO)", int((df.effect_type == "MONO").sum()))
                    m2.metric("Efeitos em combinação (COMBO)", int((df.effect_type == "COMBO").sum()))
                    st.dataframe(df, use_container_width=True, hide_index=True)
