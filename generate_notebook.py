import nbformat as nbf
import os

# Cria um novo notebook
nb = nbf.v4.new_notebook()

cells = []

# =====================================================================
# Seção 0
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""# [Seção 0] Configuração

Carregando as credenciais do `.env`, inicializando os drivers `psycopg2` (PostgreSQL) e `neo4j` (Neo4j), e validando se ambas as instâncias estão ativas e respondendo.
"""))

cells.append(nbf.v4.new_code_cell("""import os
import pandas as pd
from dotenv import load_dotenv
import psycopg2
from neo4j import GraphDatabase

# Carregar variáveis de ambiente (sem hardcode)
load_dotenv(dotenv_path='../.env')

print("Iniciando testes de conexão...")

# --- PostgreSQL ---
try:
    pg_conn = psycopg2.connect(
        host=os.getenv('PG_HOST'),
        port=os.getenv('PG_PORT'),
        dbname=os.getenv('PG_DBNAME'),
        user=os.getenv('PG_USER'),
        password=os.getenv('PG_PASSWORD')
    )
    with pg_conn.cursor() as cur:
        cur.execute("SELECT 1")
    print("✅ PostgreSQL: Conexão estabelecida e ativa!")
except Exception as e:
    print(f"❌ PostgreSQL - Erro ao conectar: {e}")

# --- Neo4j ---
try:
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_user = os.getenv('NEO4J_USER')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    neo4j_driver.verify_connectivity()
    print("✅ Neo4j: Conexão estabelecida e ativa!")
except Exception as e:
    print(f"❌ Neo4j - Erro ao conectar: {e}")
"""))

# =====================================================================
# Seção 1
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""# [Seção 1] Resposta pelo PostgreSQL

**Pergunta de pesquisa:** *"Quais drogas aparecem com mais frequência em combinações perigosas, e quais são os efeitos colaterais mais comuns que essas combinações produzem?"*

### Como o Relacional resolve isso de forma natural:
O modelo relacional trata essa pergunta aplicando operações matemáticas de conjunto e agregação. Como salvamos a tabela `drug_combination_effect` respeitando uma simetria (`drug_a_id < drug_b_id`) para poupar espaço, precisamos analisar a participação da droga nas duas colunas. Usamos um `UNION ALL` para combinar as perspectivas, e depois agrupamos com `GROUP BY` e contamos as ocorrências (`COUNT`, `COUNT DISTINCT`).

```sql
SELECT
    d.stitch_id,
    COALESCE(d.name, d.stitch_id)  AS drug_name,
    COUNT(*)                        AS n_combination_effects,
    COUNT(DISTINCT dce.se_id)       AS n_distinct_side_effects,
    COUNT(DISTINCT dce.partner_id)  AS n_drug_partners
FROM drug d
JOIN (
    SELECT drug_a_id AS drug_id, drug_b_id AS partner_id, se_id
    FROM drug_combination_effect
    UNION ALL
    SELECT drug_b_id AS drug_id, drug_a_id AS partner_id, se_id
    FROM drug_combination_effect
) dce ON d.drug_id = dce.drug_id
GROUP BY d.drug_id, d.stitch_id, d.name
ORDER BY n_combination_effects DESC
LIMIT 10;
```
"""))

cells.append(nbf.v4.new_code_cell("""sql_query = \"\"\"
SELECT
    d.stitch_id,
    COALESCE(d.name, d.stitch_id)  AS drug_name,
    COUNT(*)                        AS n_combination_effects,
    COUNT(DISTINCT dce.se_id)       AS n_distinct_side_effects,
    COUNT(DISTINCT dce.partner_id)  AS n_drug_partners
FROM drug d
JOIN (
    SELECT drug_a_id AS drug_id, drug_b_id AS partner_id, se_id
    FROM drug_combination_effect
    UNION ALL
    SELECT drug_b_id AS drug_id, drug_a_id AS partner_id, se_id
    FROM drug_combination_effect
) dce ON d.drug_id = dce.drug_id
GROUP BY d.drug_id, d.stitch_id, d.name
ORDER BY n_combination_effects DESC
LIMIT 10;
\"\"\"

# Executando via psycopg2 e carregando diretamente para o pandas
df_pg = pd.read_sql(sql_query, pg_conn)

print("🏆 Top 10 Drogas em Combinações (PostgreSQL):")
display(df_pg)
"""))

# =====================================================================
# Seção 2
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""# [Seção 2] Resposta pelo Neo4j

**Pergunta de pesquisa:** *"Quais drogas aparecem com mais frequência em combinações perigosas, e quais são os efeitos colaterais mais comuns que essas combinações produzem?"*

### Como o Grafo resolve isso de forma natural:
No modelo de grafos, o Neo4j não se importa com tabelas e ordenações forçadas de colunas. Ele resolve essa consulta através de **travessia de rede (pattern matching)**. Nós descrevemos o padrão visual `(d:Drug)-[r:CAUSES_COMBINED]-(other:Drug)` sem direcionamento na aresta. O banco se encarrega de encontrar todos os sub-grafos que correspondam a isso, contabilizando os vizinhos e arestas perfeitamente.

```cypher
MATCH (d:Drug)-[r:CAUSES_COMBINED]-(other:Drug)
WITH d,
     COUNT(r)                   AS n_combination_effects,
     COUNT(DISTINCT r.se_id)    AS n_distinct_side_effects,
     COUNT(DISTINCT other)      AS n_drug_partners
RETURN d.stitch_id              AS stitch_id,
       COALESCE(d.name, d.stitch_id) AS drug_name,
       n_combination_effects,
       n_distinct_side_effects,
       n_drug_partners
ORDER BY n_combination_effects DESC
LIMIT 10;
```
"""))

cells.append(nbf.v4.new_code_cell("""cypher_query = \"\"\"
MATCH (d:Drug)-[r:CAUSES_COMBINED]-(other:Drug)
WITH d,
     COUNT(r)                   AS n_combination_effects,
     COUNT(DISTINCT r.se_id)    AS n_distinct_side_effects,
     COUNT(DISTINCT other)      AS n_drug_partners
RETURN d.stitch_id              AS stitch_id,
       COALESCE(d.name, d.stitch_id) AS drug_name,
       n_combination_effects,
       n_distinct_side_effects,
       n_drug_partners
ORDER BY n_combination_effects DESC
LIMIT 10;
\"\"\"

# Executando via neo4j driver
with neo4j_driver.session() as session:
    result = session.run(cypher_query)
    records = [record.data() for record in result]
    
df_neo4j = pd.DataFrame(records)

print("🏆 Top 10 Drogas em Combinações (Neo4j):")
display(df_neo4j)
"""))

# =====================================================================
# Seção 3
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""# [Seção 3] Visualização com pyvis

Aqui pegamos as **3 drogas do topo** do Neo4j e plotamos a teia interativa delas usando o `pyvis`. O objetivo é descer do nível matemático de agregação (linhas e colunas) e mostrar a realidade conectada e densa da polifarmácia.

**Padrão visual:**
- **Azul (#4A90D9)**: Drogas interagindo.
- **Vermelho (#E74C3C)**: Os efeitos colaterais resultantes representados como a conexão (hub) para entendimento visual.
"""))

cells.append(nbf.v4.new_code_cell("""from pyvis.network import Network
import IPython

# Query foca nas top 3 drogas (limit 3 no subquery) e busca suas arestas com limite de visualização
cypher_viz = \"\"\"
MATCH (d:Drug)-[r:CAUSES_COMBINED]-(other:Drug)
WITH d, count(r) as freq
ORDER BY freq DESC LIMIT 3
MATCH (d)-[r:CAUSES_COMBINED]-(other:Drug)
RETURN d.stitch_id AS d1_id, coalesce(d.name, d.stitch_id) AS d1_name,
       other.stitch_id AS d2_id, coalesce(other.name, other.stitch_id) AS d2_name,
       r.se_name AS effect_name
LIMIT 250 // Limite para evitar travamento no navegador do jupyter
\"\"\"

# Criação da rede interativa
net = Network(height='600px', width='100%', notebook=True, directed=False)

with neo4j_driver.session() as session:
    result = session.run(cypher_viz)
    for record in result:
        d1_id = record['d1_id']
        d1_name = record['d1_name']
        d2_id = record['d2_id']
        d2_name = record['d2_name']
        effect_name = record['effect_name']
        
        # Adiciona Drogas (Azul)
        net.add_node(d1_id, label=d1_name, color='#4A90D9', title=f"Drug: {d1_name}")
        net.add_node(d2_id, label=d2_name, color='#4A90D9', title=f"Drug: {d2_name}")
        
        # Adiciona Efeito Colateral (Vermelho e Quadrado) como intermediário para visualizar a aresta multi-dimensional
        effect_node_id = f"{d1_id}_{d2_id}_{effect_name}"
        net.add_node(effect_node_id, label=effect_name, color='#E74C3C', shape='box', size=15, title=f"Effect: {effect_name}")
        
        # Liga as drogas no efeito
        net.add_edge(d1_id, effect_node_id, color='#95a5a6')
        net.add_edge(effect_node_id, d2_id, color='#95a5a6')

# Salva e exibe a visualização
net.show('demo_grafos.html')
"""))

# =====================================================================
# Seção 4
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""# [Seção 4] Reflexão e Comparação Dual-Paradigma

| Aspecto | PostgreSQL (Relacional) | Neo4j (Grafo) |
| :--- | :--- | :--- |
| **Abordagem Natural** | Agregação (`GROUP BY`), contagem de registros, conjuntos (`UNION ALL`). A estrutura matemática de conjuntos é perfeita para tabelas sumarizadas. | Navegação em rede (`MATCH`), pattern matching não-direcional. Enxerga conexões não como chaves estrangeiras, mas como caminhos físicos. |
| **O que foi fácil** | Retornar matrizes bem formatadas e agrupar por múltiplos eixos. A matemática bruta de somas e agrupamentos é extremamente eficiente no relacional. | Modelar as combinações como o que elas são: interações biológicas. A query refletiu o problema em linguagem natural, isenta de contorcionismos de sintaxe (`UNION ALL`). |
| **O que seria trabalhoso** | Encontrar "caminhos" encadeados (Ex: "Mostre o caminho onde a Droga A causa Efeito X ao combinar com B, que inibe Proteína Y"). Exigiria CTEs recursivas lentas. | Executar operações de agregação de varredura global (`table scan` de todas as entidades sem nenhum ponto de ancoragem inicial na rede). |

**Conclusão**: 
O **PostgreSQL** é uma potência analítica para consolidação em massa e matemática baseada em tabelas. O **Neo4j** entrega não apenas consultas declarativas que refletem diretamente o problema semântico, mas também provê a visualização intrínseca baseada na vizinhança e no contexto de cada elemento. Na infraestrutura da saúde (como Polifarmácia), ambos os paradigmas cumprem papéis complementares indiscutíveis.
"""))

nb.cells = cells

# Cria o diretório e salva
os.makedirs('notebooks', exist_ok=True)
with open('notebooks/presentation.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Notebook presentation.ipynb criado com sucesso em notebooks/")
