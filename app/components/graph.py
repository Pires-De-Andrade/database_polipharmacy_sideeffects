"""
Construção de grafos interativos com pyvis para embutir no Streamlit.

Mantém o mesmo padrão visual do notebook de apresentação:
  • Azul  (#4A90D9): nós Drug
  • Vermelho (#E74C3C): efeitos colaterais (intermediários da aresta combinada)
  • Verde (#27AE60): proteínas
"""
from __future__ import annotations

import tempfile

import pandas as pd
from pyvis.network import Network

DRUG_COLOR = "#4A90D9"
EFFECT_COLOR = "#E74C3C"
PROTEIN_COLOR = "#27AE60"
EDGE_COLOR = "#95a5a6"


def _render(net: Network) -> str:
    """Gera o HTML do grafo pyvis como string para `st.components.v1.html`."""
    net.barnes_hut()
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        net.save_graph(f.name)
        path = f.name
    with open(path, encoding="utf-8") as f:
        return f.read()


def combo_subgraph_html(df: pd.DataFrame, height: int = 600) -> str:
    """
    Constrói o subgrafo Drug—Efeito—Drug a partir do DataFrame de
    `top_drugs_subgraph`. Cada efeito vira um nó intermediário entre as
    duas drogas, replicando a visualização da Seção 3 do notebook.
    """
    net = Network(height=f"{height}px", width="100%", directed=False, bgcolor="#ffffff")

    for _, row in df.iterrows():
        d1_id, d1_name = row["d1_id"], row["d1_name"]
        d2_id, d2_name = row["d2_id"], row["d2_name"]
        effect = row["effect_name"]

        net.add_node(d1_id, label=d1_name, color=DRUG_COLOR, title=f"Droga: {d1_name}")
        net.add_node(d2_id, label=d2_name, color=DRUG_COLOR, title=f"Droga: {d2_name}")

        effect_id = f"{d1_id}_{d2_id}_{effect}"
        net.add_node(
            effect_id, label=effect, color=EFFECT_COLOR, shape="box",
            size=12, title=f"Efeito: {effect}",
        )
        net.add_edge(d1_id, effect_id, color=EDGE_COLOR)
        net.add_edge(effect_id, d2_id, color=EDGE_COLOR)

    return _render(net)


def path_html(path_nodes: list[str], edge_types: list[str], height: int = 400) -> str:
    """
    Visualiza um caminho (lista de nós rotulados 'Drug:...'/'Protein:...')
    como uma cadeia linear, colorindo por tipo de nó.
    """
    net = Network(height=f"{height}px", width="100%", directed=False, bgcolor="#ffffff")

    for node in path_nodes:
        is_drug = node.startswith("Drug:")
        net.add_node(
            node, label=node.split(":", 1)[-1],
            color=DRUG_COLOR if is_drug else PROTEIN_COLOR,
            shape="dot" if is_drug else "diamond",
            title=node,
        )

    for i, etype in enumerate(edge_types):
        net.add_edge(path_nodes[i], path_nodes[i + 1], label=etype, color=EDGE_COLOR)

    return _render(net)
