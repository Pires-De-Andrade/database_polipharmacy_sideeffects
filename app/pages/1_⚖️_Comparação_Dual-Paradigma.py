"""
Página: Comparação Dual-Paradigma.

Reproduz o tema central do notebook de apresentação — a MESMA pergunta de
pesquisa resolvida no PostgreSQL (SQL) e no Neo4j (Cypher), lado a lado,
mostrando o código de cada um e os resultados.
"""
import streamlit as st

from backend import queries

st.set_page_config(page_title="Comparação Dual-Paradigma", page_icon="⚖️", layout="wide")

st.title("⚖️ Comparação Dual-Paradigma")
st.markdown(
    "> **Pergunta de pesquisa:** *Quais drogas aparecem com mais frequência em "
    "combinações perigosas, e quantos efeitos colaterais distintos essas "
    "combinações produzem?*"
)

limit = st.slider("Número de drogas no ranking (LIMIT)", 5, 25, 10)
run = st.button("▶️ Executar nos dois bancos", type="primary")

col_pg, col_neo = st.columns(2)

with col_pg:
    st.subheader("🐘 PostgreSQL — Relacional")
    st.caption(
        "Resolve por **agregação e conjuntos**: `UNION ALL` une a participação da "
        "droga nas posições A e B (a tabela guarda `drug_a_id < drug_b_id`), depois "
        "`GROUP BY` + `COUNT`."
    )
    st.code(queries.DANGEROUS_DRUGS_SQL.replace("%(limit)s", str(limit)), language="sql")

with col_neo:
    st.subheader("🕸️ Neo4j — Grafo")
    st.caption(
        "Resolve por **pattern matching**: o padrão não-direcional "
        "`(d:Drug)-[r:CAUSES_COMBINED]-(other:Drug)` captura a droga em ambas as "
        "direções sem `UNION` — a query reflete o problema diretamente."
    )
    st.code(queries.DANGEROUS_DRUGS_CYPHER.replace("$limit", str(limit)), language="cypher")

if run:
    col_pg_r, col_neo_r = st.columns(2)
    with col_pg_r:
        try:
            with st.spinner("Executando SQL…"):
                df_pg = queries.dangerous_drugs_sql(limit)
            st.dataframe(df_pg, use_container_width=True, hide_index=True)
            st.bar_chart(df_pg.set_index("drug_name")["n_combination_effects"])
        except Exception as e:  # noqa: BLE001
            st.error(f"Falha no PostgreSQL: {e}")
    with col_neo_r:
        try:
            with st.spinner("Executando Cypher…"):
                df_neo = queries.dangerous_drugs_cypher(limit)
            st.dataframe(df_neo, use_container_width=True, hide_index=True)
            st.bar_chart(df_neo.set_index("drug_name")["n_combination_effects"])
        except Exception as e:  # noqa: BLE001
            st.error(f"Falha no Neo4j: {e}")

st.divider()
with st.expander("📌 Reflexão: quando cada paradigma vence"):
    st.markdown(
        """
| Aspecto | PostgreSQL (Relacional) | Neo4j (Grafo) |
|---|---|---|
| **Abordagem natural** | Agregação (`GROUP BY`), conjuntos (`UNION ALL`) | Navegação em rede (`MATCH`), pattern matching |
| **Fácil** | Matrizes sumarizadas, matemática de somas/agrupamentos | Modelar combinações como interações; query legível |
| **Trabalhoso** | Encontrar *caminhos* encadeados (CTEs recursivas) | Agregação por varredura global sem ponto de ancoragem |

**Conclusão:** o PostgreSQL é potência analítica para consolidação em massa;
o Neo4j entrega consultas declarativas que refletem o problema semântico e
visualização baseada em vizinhança. Em saúde, são complementares.
"""
    )
