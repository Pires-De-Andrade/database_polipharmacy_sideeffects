"""
Tab EXPERIMENTAL — Interação Indirecta via rede PPI.

Mecanismo central do DECAGON: dois medicamentos podem interagir mesmo sem
partilharem um alvo directo, desde que os seus alvos estejam ligados na rede
de interacção proteína-proteína (PPI). Esta aba revela essas "pontes":

    (Drug A)-[:TARGETS]->(pa)-[:INTERACTS_WITH]-(pb)<-[:TARGETS]-(Drug B)

Fica escondida atrás do menu "⋮" porque é experimental — só é mostrada se
funcionar de forma fiável durante a apresentação.
"""
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from app.backend.queries.cypher_loader import load_cypher, run_cypher
from app.backend.drug_names import resolve_name
from app.frontend.layout import render_query_footer
from app.utils.timer import QueryTimer

# Cores (alinhadas com os outros componentes)
COL_DRUG = "#1B3A5C"        # azul escuro — medicamentos
COL_PROT_A = "#27AE60"      # verde — alvos do medicamento A
COL_PROT_B = "#8E44AD"      # roxo — alvos do medicamento B
COL_BRIDGE = "#E67E22"      # laranja — aresta PPI (a ponte)
COL_TARGET_EDGE = "#c0c8d0"  # cinza — aresta TARGETS


def _build_pyvis_html(rows: list[dict], name_a: str, name_b: str,
                      stitch_a: str, stitch_b: str) -> str:
    """Constrói o grafo bipartido das pontes indirectas e retorna o HTML."""
    net = Network(height="520px", width="100%", notebook=False, directed=False)
    net.barnes_hut(gravity=-4000, spring_length=180)

    # Nós dos medicamentos
    net.add_node(stitch_a, label=name_a, color=COL_DRUG, size=30, shape="dot",
                 title=f"Drug: {name_a} ({stitch_a})",
                 font={"size": 14, "color": COL_DRUG, "bold": True})
    net.add_node(stitch_b, label=name_b, color=COL_DRUG, size=30, shape="dot",
                 title=f"Drug: {name_b} ({stitch_b})",
                 font={"size": 14, "color": COL_DRUG, "bold": True})

    added_nodes: set[str] = set()
    added_edges: set[tuple[str, str]] = set()

    def _edge(src: str, dst: str, color: str, width: int, dashes: bool = False):
        key = tuple(sorted((src, dst)))
        if key in added_edges:
            return
        added_edges.add(key)
        net.add_edge(src, dst, color=color, width=width, dashes=dashes)

    for r in rows:
        # Lados separados (a_/b_) para deixar a ponte visualmente explícita,
        # mesmo que o mesmo gene apareça nos dois lados.
        aid = f"a_{r['a_gene']}"
        bid = f"b_{r['b_gene']}"

        if aid not in added_nodes:
            added_nodes.add(aid)
            net.add_node(aid, label=str(r["a_name"]), color=COL_PROT_A, size=14,
                         shape="dot", title=f"Alvo de {name_a}: {r['a_name']} (Gene {r['a_gene']})",
                         font={"size": 10, "color": "#1a6b3c"})
        if bid not in added_nodes:
            added_nodes.add(bid)
            net.add_node(bid, label=str(r["b_name"]), color=COL_PROT_B, size=14,
                         shape="dot", title=f"Alvo de {name_b}: {r['b_name']} (Gene {r['b_gene']})",
                         font={"size": 10, "color": "#5b2c6f"})

        _edge(stitch_a, aid, COL_TARGET_EDGE, 1)
        _edge(stitch_b, bid, COL_TARGET_EDGE, 1)
        _edge(aid, bid, COL_BRIDGE, 2, dashes=True)  # a ponte PPI

    return net.generate_html()


def render_indirect_ppi(data: dict):
    """Renderiza a aba experimental de interacção indirecta via PPI."""
    st.markdown("##### 🧪 Interação Indireta via Rede PPI — *experimental*")
    st.markdown(
        '<div class="interpretation-panel">'
        "O mecanismo central do <strong>DECAGON</strong>: dois medicamentos podem "
        "interagir mesmo <strong>sem partilharem um alvo directo</strong>, desde que "
        "os seus alvos estejam ligados na rede de interacção proteína-proteína (PPI). "
        "Cada linha tracejada laranja é uma <strong>ponte molecular</strong> entre um "
        "alvo de A e um alvo de B."
        "</div>",
        unsafe_allow_html=True,
    )

    stitch_a = data.get("stitch_a")
    stitch_b = data.get("stitch_b")

    if not stitch_a or not stitch_b:
        st.warning("Não foi possível resolver os identificadores STITCH dos medicamentos.")
        return

    gd = data.get("graph_data", {})
    name_a = gd.get("drug_a", {}).get("name") or resolve_name(stitch_a)
    name_b = gd.get("drug_b", {}).get("name") or resolve_name(stitch_b)

    # ── Executar a query ──────────────────────────────────────────────────
    try:
        with st.spinner("A procurar pontes na rede PPI…"):
            with QueryTimer() as t:
                rows = run_cypher(
                    "streamlit_indirect_ppi.cypher",
                    {"stitch_a": stitch_a, "stitch_b": stitch_b},
                )
    except Exception as e:  # noqa: BLE001 — feature experimental, falha graciosa
        st.error("A consulta de interação indireta falhou neste momento.")
        st.caption(f"Detalhe: {e}")
        return

    if not rows:
        st.info(
            "Nenhuma ponte indireta encontrada: os alvos destes medicamentos não "
            "estão directamente ligados na rede PPI (ou algum deles não tem alvos "
            "registados)."
        )
        render_query_footer("Neo4j", t.elapsed_ms)
        return

    # ── Métricas ──────────────────────────────────────────────────────────
    n_bridges = len(rows)
    prot_a = len({r["a_gene"] for r in rows})
    prot_b = len({r["b_gene"] for r in rows})
    truncated = n_bridges >= 300

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Pontes PPI", f"{n_bridges}{'+' if truncated else ''}")
    with c2:
        st.metric(f"Alvos de A envolvidos", prot_a)
    with c3:
        st.metric(f"Alvos de B envolvidos", prot_b)

    if truncated:
        st.caption("⚠️ Resultado limitado a 300 pontes para manter o grafo legível.")

    # ── Grafo ─────────────────────────────────────────────────────────────
    html = _build_pyvis_html(rows, name_a, name_b, stitch_a, stitch_b)
    components.html(html, height=540, scrolling=False)

    legend = st.columns(4)
    with legend[0]:
        st.markdown("🔵 **Azul** — Medicamentos")
    with legend[1]:
        st.markdown("🟢 **Verde** — Alvos de A")
    with legend[2]:
        st.markdown("🟣 **Roxo** — Alvos de B")
    with legend[3]:
        st.markdown("🟠 **Tracejado** — Ponte PPI")

    render_query_footer("Neo4j", t.elapsed_ms)
