"""
Página: Visualização de Grafo.

Explora a força do Neo4j — relações como caminhos físicos. Inclui o subgrafo
das drogas mais conectadas (modelo da Seção 3 do notebook), proteínas
compartilhadas entre duas drogas e o caminho mais curto entre drogas.
"""
import streamlit as st
import streamlit.components.v1 as components

from backend import queries
from components import graph

st.set_page_config(page_title="Visualização de Grafo", page_icon="🕸️", layout="wide")

st.title("🕸️ Visualização de Grafo")
st.caption("Onde o grafo brilha: enxergar a polifarmácia como rede conectada. *Fonte: Neo4j.*")

tab_sub, tab_shared, tab_path = st.tabs(
    ["🔮 Teia das drogas mais conectadas", "🧬 Proteínas compartilhadas", "🛣️ Caminho mais curto"]
)

# ── Subgrafo das top drogas ─────────────────────────────────────────────────────
with tab_sub:
    st.subheader("Subgrafo Droga — Efeito — Droga")
    st.markdown(
        "Cada **efeito colateral** (vermelho) aparece como ponte entre as duas "
        "**drogas** (azul) que o causam em combinação."
    )
    c1, c2 = st.columns(2)
    top_drugs = c1.slider("Quantas drogas (mais conectadas)", 2, 8, 3)
    edge_limit = c2.slider("Limite de arestas (performance)", 50, 500, 250, step=50)
    if st.button("Gerar teia", type="primary", key="web"):
        try:
            with st.spinner("Consultando Neo4j e montando o grafo…"):
                df = queries.top_drugs_subgraph(top_drugs, edge_limit)
            if df.empty:
                st.info("Nenhuma aresta retornada.")
            else:
                components.html(graph.combo_subgraph_html(df), height=620)
                st.caption(f"{len(df)} arestas de combinação renderizadas.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Falha no Neo4j: {e}")


# ── Proteínas compartilhadas ────────────────────────────────────────────────────
with tab_shared:
    st.subheader("Proteínas-alvo compartilhadas entre duas drogas")
    st.markdown(
        "Hipótese central de Zitnik et al. (2018): efeitos de polifarmácia se "
        "correlacionam com **alvos proteicos compartilhados**."
    )
    drugs = None
    try:
        drugs = queries.drug_list(2000)
    except Exception as e:  # noqa: BLE001
        st.error(f"Não foi possível carregar a lista de drogas: {e}")

    if drugs is not None and not drugs.empty:
        opts = drugs["stitch_id"].tolist()
        c1, c2 = st.columns(2)
        da = c1.selectbox("Droga A", opts, index=0, key="sp_a")
        db = c2.selectbox("Droga B", opts, index=min(1, len(opts) - 1), key="sp_b")
        if st.button("Buscar proteínas compartilhadas", key="shared"):
            try:
                df = queries.shared_proteins(da, db)
                if df.empty:
                    st.info("Essas duas drogas não compartilham proteínas-alvo no grafo.")
                else:
                    st.metric("Proteínas compartilhadas", len(df))
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:  # noqa: BLE001
                st.error(f"Falha no Neo4j: {e}")


# ── Caminho mais curto ──────────────────────────────────────────────────────────
with tab_path:
    st.subheader("Caminho mais curto entre duas drogas")
    st.markdown(
        "Via rede de alvos (`TARGETS`) e interações proteína-proteína "
        "(`INTERACTS_WITH`), até 4 saltos. Caminhos curtos sugerem proximidade "
        "farmacológica — algo **natural no grafo e custoso no relacional**."
    )
    drugs = None
    try:
        drugs = queries.drug_list(2000)
    except Exception as e:  # noqa: BLE001
        st.error(f"Não foi possível carregar a lista de drogas: {e}")

    if drugs is not None and not drugs.empty:
        opts = drugs["stitch_id"].tolist()
        c1, c2 = st.columns(2)
        da = c1.selectbox("Droga A", opts, index=0, key="pa")
        db = c2.selectbox("Droga B", opts, index=min(1, len(opts) - 1), key="pb")
        if st.button("Encontrar caminho", key="path"):
            try:
                df = queries.shortest_path(da, db)
                if df.empty:
                    st.info("Nenhum caminho de até 4 saltos entre essas drogas.")
                else:
                    row = df.iloc[0]
                    st.metric("Comprimento do caminho", int(row["path_length"]))
                    st.write(" → ".join(row["path_nodes"]))
                    components.html(
                        graph.path_html(row["path_nodes"], row["edge_types"]),
                        height=420,
                    )
            except Exception as e:  # noqa: BLE001
                st.error(f"Falha no Neo4j: {e}")
