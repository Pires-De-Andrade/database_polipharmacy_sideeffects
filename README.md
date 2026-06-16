# Projeto de Banco de Dados

Modelagem de efeitos colaterais de polifarmácia (uso simultâneo de múltiplos medicamentos) usando bancos relacional e de grafos.

Baseado em: Zitnik et al. (2018). *"Modeling polypharmacy side effects with graph convolutional networks"*, Bioinformatics 34(13). Datasets do projeto [DECAGON/SNAP Stanford](http://snap.stanford.edu/decagon).

## Visão Geral

| Componente | Tecnologia |
|-----------|-----------|
| Banco relacional | PostgreSQL 16 |
| Banco de grafos | Neo4j 5 Community |
| ETL | Python 3.11+ (pandas, psycopg2, neo4j) |
| Versionamento | Git/GitHub |

## Estrutura do Projeto

```
projeto-bd-polifarmacia/
├── README.md                          # ← este arquivo
├── .gitignore
├── data/                              # CSVs do DECAGON (não versionados)
│   ├── bio-decagon-ppi.csv
│   ├── bio-decagon-targets.csv
│   ├── bio-decagon-combo.csv
│   ├── bio-decagon-mono.csv
│   └── bio-decagon-effectcategories.csv
├── sql/
│   ├── schema.sql                     # DDL — CREATE TABLE, constraints
│   ├── indexes.sql                    # Índices de performance
│   ├── views.sql                      # Views analíticas
│   └── queries/                       # Consultas SQL avulsas
├── cypher/
│   ├── constraints.cypher             # Constraints Neo4j
│   └── queries/                       # Consultas Cypher avulsas
├── etl/
│   ├── requirements.txt               # Dependências Python
│   ├── load_relational.py             # ETL → PostgreSQL
│   └── load_graph.py                  # ETL → Neo4j
└── docs/
    └── schema.md                      # Documentação do modelo de dados
```

## Configuração do Ambiente

### 1. Pré-requisitos

- **Python 3.11+**: [Download](https://www.python.org/downloads/)
- **PostgreSQL 16**: [Download](https://www.postgresql.org/download/)
- **Neo4j 5 Community**: [Download](https://neo4j.com/download/)

### 2. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/projeto-bd-polifarmacia.git
cd projeto-bd-polifarmacia
```

### 3. Baixar os datasets

Faça download dos CSVs do DECAGON e coloque-os na pasta `data/`:

```bash
mkdir -p data
cd data
# Baixar de http://snap.stanford.edu/decagon
# Arquivos necessários:
#   bio-decagon-ppi.csv
#   bio-decagon-targets.csv
#   bio-decagon-combo.csv
#   bio-decagon-mono.csv
#   bio-decagon-effectcategories.csv
cd ..
```

### 4. Ambiente virtual Python

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r etl/requirements.txt
```

### 5. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

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

### 6. Criar o banco PostgreSQL

```bash
# Via psql
createdb polifarmacia

# Ou via SQL
psql -U postgres -c "CREATE DATABASE polifarmacia;"
```

## Carga de Dados

### PostgreSQL (carga relacional)

```bash
# Carga completa (pode levar alguns minutos para o combo.csv)
python etl/load_relational.py

# Teste rápido com amostra de 1000 linhas por CSV
python etl/load_relational.py --sample 1000

# Pular o combo (4.65M linhas) para testes
python etl/load_relational.py --skip-combo

# Pular criação do schema (se já existir)
python etl/load_relational.py --no-schema
```

O script:
1. Executa `sql/schema.sql` e `sql/indexes.sql`
2. Carrega entidades base: `side_effect`, `drug`, `protein`
3. Carrega relacionamentos: `drug_protein_target`, `protein_interaction`
4. Carrega efeitos: `drug_mono_effect`, `drug_combination_effect`
5. Exibe resumo de contagens ao final

### Neo4j (carga de grafos)

```bash
# Carga completa (pode levar alguns minutos para o combo)
python etl/load_graph.py

# Teste rápido com amostra de 1000 linhas por CSV
python etl/load_graph.py --sample 1000

# Pular o combo (4.65M arestas) para testes
python etl/load_graph.py --skip-combo

# Pular criação de constraints (se já existirem)
python etl/load_graph.py --no-constraints
```

## Modelo de Dados

Consulte a documentação completa em [`docs/schema.md`](docs/schema.md).

### Resumo dos Datasets

| Dataset | Registros | Descrição |
|---------|----------|-----------|
| PPI | 719.402 | Interações proteína-proteína |
| Targets | 18.596 | Droga → proteína-alvo |
| Combo (TWOSIDES) | ~4.651.131 | Efeitos de pares de drogas |
| Mono (SIDER/OFFSIDES) | ~487.000 | Efeitos de drogas individuais |
| Effect Categories | 964 | Classificação dos efeitos |

## Queries de Exemplo

### PostgreSQL

```sql
-- Top 10 efeitos colaterais mais frequentes em combinações de drogas
SELECT se.name, se.category, COUNT(*) AS freq
FROM drug_combination_effect dce
JOIN side_effect se ON dce.se_id = se.se_id
GROUP BY se.name, se.category
ORDER BY freq DESC
LIMIT 10;

-- Drogas com mais alvos proteicos
SELECT d.stitch_id, COUNT(*) AS n_targets
FROM drug_protein_target dpt
JOIN drug d ON dpt.drug_id = d.drug_id
GROUP BY d.stitch_id
ORDER BY n_targets DESC
LIMIT 10;
```

### Cypher (Neo4j)

```cypher
// Caminho mais curto entre duas drogas via proteínas compartilhadas
MATCH path = shortestPath(
  (d1:Drug {stitch_id:'CID000002173'})-[*]-(d2:Drug {stitch_id:'CID000003345'})
)
RETURN path;
```

## Referências

- Zitnik, M., Agrawal, M., & Leskovec, J. (2018). *Modeling polypharmacy side effects with graph convolutional networks*. Bioinformatics, 34(13), i457–i466.
- [DECAGON — SNAP Stanford](http://snap.stanford.edu/decagon)
- [STITCH Database](http://stitch.embl.de/)
- [SIDER — Side Effect Resource](http://sideeffects.embl.de/)

Projeto de Banco de Dados
