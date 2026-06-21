"""
Tab 2 — Contexto Molecular (Neo4j + pyvis).

Constrói e renderiza o grafo interactivo com proteínas-alvo partilhadas
e exclusivas de cada medicamento.
"""
import streamlit as st
import streamlit.components.v1 as components

from pyvis.network import Network

from app.frontend.layout import render_query_footer


def _build_pyvis_html(graph_data: dict) -> str:
    """Constrói o grafo pyvis e retorna o HTML como string."""
    net = Network(height="500px", width="100%", notebook=False, directed=False)
    net.barnes_hut(gravity=-3000, spring_length=150)

    drug_a = graph_data["drug_a"]
    drug_b = graph_data["drug_b"]
    shared = graph_data.get("shared_proteins", [])
    excl_a = graph_data.get("exclusive_a_proteins", [])
    excl_b = graph_data.get("exclusive_b_proteins", [])

    # ── Nós: Medicamentos (azul escuro, grandes) ─────────────────────────
    net.add_node(
        drug_a["stitch_id"],
        label=drug_a["name"],
        color="#1B3A5C",
        size=30,
        shape="dot",
        title=f"Drug: {drug_a['name']} ({drug_a['stitch_id']})",
        font={"size": 14, "color": "#1B3A5C", "bold": True},
    )
    net.add_node(
        drug_b["stitch_id"],
        label=drug_b["name"],
        color="#1B3A5C",
        size=30,
        shape="dot",
        title=f"Drug: {drug_b['name']} ({drug_b['stitch_id']})",
        font={"size": 14, "color": "#1B3A5C", "bold": True},
    )

    # ── Nós: Proteínas partilhadas (laranja, destaque) ───────────────────
    for p in shared:
        node_id = f"prot_{p['gene_id']}"
        net.add_node(
            node_id,
            label=p["name"],
            color="#E67E22",
            size=20,
            shape="diamond",
            title=f"Proteína partilhada: {p['name']} (Gene {p['gene_id']})",
            font={"size": 11, "color": "#8B4513"},
        )
        net.add_edge(drug_a["stitch_id"], node_id, color="#aabbcc", width=2)
        net.add_edge(drug_b["stitch_id"], node_id, color="#aabbcc", width=2)

    # ── Nós: Proteínas exclusivas de A (verde) ───────────────────────────
    for p in excl_a:
        node_id = f"prot_{p['gene_id']}"
        net.add_node(
            node_id,
            label=p["name"],
            color="#27AE60",
            size=15,
            shape="dot",
            title=f"Alvo exclusivo de {drug_a['name']}: {p['name']} (Gene {p['gene_id']})",
            font={"size": 10, "color": "#1a6b3c"},
        )
        net.add_edge(drug_a["stitch_id"], node_id, color="#c5e1cc", width=1)

    # ── Nós: Proteínas exclusivas de B (verde) ───────────────────────────
    for p in excl_b:
        node_id = f"prot_{p['gene_id']}"
        net.add_node(
            node_id,
            label=p["name"],
            color="#27AE60",
            size=15,
            shape="dot",
            title=f"Alvo exclusivo de {drug_b['name']}: {p['name']} (Gene {p['gene_id']})",
            font={"size": 10, "color": "#1a6b3c"},
        )
        net.add_edge(drug_b["stitch_id"], node_id, color="#c5e1cc", width=1)

    return net.generate_html()


def render_molecular_graph(data: dict):
    """Renderiza a Tab 2 com o grafo pyvis e painel de interpretação."""
    graph_data = data.get("graph_data", {})
    n_shared = data.get("shared_proteins", 0)

    if not graph_data:
        st.markdown(
            '<div class="not-found-panel">'
            "Contexto molecular não disponível para esta combinação no Neo4j."
            "</div>",
            unsafe_allow_html=True,
        )
        render_query_footer("Neo4j", data["cypher_time_ms"])
        return

    # ── Grafo interactivo ─────────────────────────────────────────────────
    st.markdown("##### Rede de Alvos Moleculares")

    html_content = _build_pyvis_html(graph_data)
    components.html(html_content, height=520, scrolling=False)

    # ── Legenda visual ────────────────────────────────────────────────────
    legend_cols = st.columns(3)
    with legend_cols[0]:
        st.markdown("🔵 **Azul escuro** — Medicamentos")
    with legend_cols[1]:
        st.markdown("🟠 **Laranja** — Proteínas partilhadas")
    with legend_cols[2]:
        st.markdown("🟢 **Verde** — Proteínas exclusivas")

    # ── Painel de interpretação ───────────────────────────────────────────
    if n_shared > 0:
        plural = "s" if n_shared > 1 else ""
        st.markdown(
            f'<div class="interpretation-panel">'
            f"Estes medicamentos partilham <strong>{n_shared} proteína{plural}-alvo</strong>. "
            f"A sobreposição de alvos moleculares é o mecanismo que "
            f"explica a interacção farmacológica."
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="interpretation-panel">'
            "Estes medicamentos não partilham proteínas-alvo conhecidas. "
            "A interacção pode ser farmacocinética ou ainda não documentada."
            "</div>",
            unsafe_allow_html=True,
        )

    # ── Rodapé ────────────────────────────────────────────────────────────
    render_query_footer("Neo4j", data["cypher_time_ms"])
