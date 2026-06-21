# Projeto Acadêmico de Bancos de Dados: Polifarmácia

Modelagem de efeitos colaterais de polifarmácia (uso simultâneo de múltiplos medicamentos) usando uma abordagem **Dual-Paradigma** com bancos relacional (PostgreSQL) e de grafos (Neo4j).

Baseado no dataset do artigo: Zitnik et al. (2018). *"Modeling polypharmacy side effects with graph convolutional networks"*, Bioinformatics 34(13). [DECAGON/SNAP Stanford](http://snap.stanford.edu/decagon).

---

## 🎯 Visão Geral

O entregável principal deste projeto é o **Sistema de Consulta de Risco Farmacológico**, uma aplicação web desenvolvida em Streamlit que demonstra o contraste e a complementaridade entre os paradigmas relacional e de grafos.

| Componente | Tecnologia |
|-----------|-----------|
| **Frontend/App** | Streamlit, Plotly, Pyvis |
| **Banco Relacional** | PostgreSQL 16 |
| **Banco de Grafos** | Neo4j 5 Community |
| **ETL / Backend** | Python 3.11+ (pandas, psycopg2, neo4j) |

---

## 📂 Estrutura do Projeto

```text
projeto-bd-polifarmacia/
├── app/                               # Aplicação Streamlit
│   ├── main.py                        # Ponto de entrada da aplicação
│   ├── backend/                       # Conexões e loaders de queries
│   ├── frontend/                      # Componentes visuais e layout
│   └── utils/                         # Utilitários (ex: timer)
├── cypher/                            # Scripts Neo4j
│   ├── constraints.cypher             # Índices e constraints
│   └── queries/                       # Consultas Cypher (usadas na app e testes)
├── sql/                               # Scripts PostgreSQL
│   ├── schema.sql                     # Tabelas e restrições
│   ├── indexes.sql                    # Otimização de performance
│   └── queries/                       # Consultas SQL (usadas na app e analíticas)
├── etl/                               # Pipeline de Ingestão de Dados
│   ├── load_relational.py             # ETL → PostgreSQL
│   └── load_graph.py                  # ETL → Neo4j
├── data/                              # CSVs do DECAGON (não versionados)
├── requirements.txt                   # Dependências do projeto
└── README.md                          # Documentação principal
```

---

## 🚀 Como Executar o Projeto

### 1. Pré-requisitos
- Python 3.11+
- PostgreSQL 16
- Neo4j 5 Community

### 2. Configurar o Ambiente

Clone o repositório e crie o ambiente virtual:

```bash
git clone https://github.com/seu-usuario/projeto-bd-polifarmacia.git
cd projeto-bd-polifarmacia

python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto com as suas credenciais:
```env
# PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_DBNAME=polifarmacia
PG_USER=postgres
PG_PASSWORD=sua_senha_aqui

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=sua_senha_aqui
```

### 3. Carga de Dados (ETL)

Crie o banco de dados PostgreSQL (`createdb polifarmacia`) e certifique-se de que o Neo4j está a correr.
Coloque os ficheiros CSV do Decagon na pasta `data/` e corra os scripts de ETL:

```bash
# Carga Relacional (PostgreSQL)
python etl/load_relational.py

# Carga de Grafos (Neo4j)
python etl/load_graph.py
```
*(Nota: a carga do ficheiro combo.csv pode demorar alguns minutos devido ao elevado volume de dados - 4.65M registos).*

### 4. Executar a Aplicação (Frontend)

Com a base de dados populada, inicie a interface de consulta clínica:

```bash
streamlit run app/main.py
```
A aplicação abrirá automaticamente no seu navegador padrão (geralmente `http://localhost:8501`).

---

## 💡 O Paradigma Dual

A aplicação apresenta três abas que ilustram a arquitectura do projeto:
1. **Perfil de Risco (PostgreSQL):** Excelente para navegação estruturada, agrupar efeitos colaterais e calcular contagens exactas. Responde ao **quê** e **com que frequência**.
2. **Contexto Molecular (Neo4j):** Excelente para travessia de dados complexos, revelando a vizinhança molecular e as proteínas-alvo partilhadas pelos medicamentos. Responde ao **porquê** da interacção.
3. **Comparação de Paradigmas:** Exibe as queries exactas que a aplicação gerou em tempo real e compara a latência de execução entre o motor SQL e o Cypher.

## 📚 Referências

- Zitnik, M., Agrawal, M., & Leskovec, J. (2018). *Modeling polypharmacy side effects with graph convolutional networks*. Bioinformatics, 34(13), i457–i466.
- [DECAGON — SNAP Stanford](http://snap.stanford.edu/decagon)
- [STITCH Database](http://stitch.embl.de/)
- [SIDER — Side Effect Resource](http://sideeffects.embl.de/)
