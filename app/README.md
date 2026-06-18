# App de Demonstração — Polifarmácia (Streamlit)

Aplicação web que demonstra o projeto de banco de dados de **efeitos colaterais
de polifarmácia** comparando os dois paradigmas (**PostgreSQL** × **Neo4j**),
ambos hospedados na **GCP**.

## O que ela faz

| Página | Descrição |
|--------|-----------|
| 🏠 **Home** | Visão geral + status das conexões com os bancos |
| ⚖️ **Comparação Dual-Paradigma** | A mesma pergunta resolvida em SQL e Cypher, lado a lado (código + resultado) |
| 🔬 **Explorador Analítico** | Hub drugs, efeitos comuns/emergentes, pares perigosos, análise por categoria, hubs de proteína, perfil de risco de droga |
| 🕸️ **Visualização de Grafo** | Teia interativa das drogas mais conectadas, proteínas compartilhadas e caminho mais curto entre drogas |

## Arquitetura

```
app/
├── Home.py                 # entrypoint Streamlit (status + overview)
├── pages/                  # páginas (multipage nativo do Streamlit)
├── backend/                # camada de dados (separada da UI)
│   ├── config.py           #   lê o .env da raiz (mesmas vars dos ETLs)
│   ├── db.py               #   conexões PG/Neo4j cacheadas + status
│   └── queries.py          #   lógica de negócio: queries SQL/Cypher → DataFrame
├── components/graph.py     # visualização de grafos (pyvis)
└── requirements.txt
```

A camada **backend** reaproveita as consultas versionadas em
[`../sql/queries/`](../sql/queries/) e [`../cypher/queries/`](../cypher/queries/);
a UI nunca fala diretamente com os drivers.

## Como rodar

```bash
# 1. Configurar credenciais (na raiz do projeto)
cp .env.example .env
# edite o .env com os dados das instâncias GCP

# 2. Ambiente virtual + dependências
python -m venv venv && source venv/bin/activate
pip install -r app/requirements.txt

# 3. Subir a app
streamlit run app/Home.py
```

A app abre em `http://localhost:8501`. A página **Home** mostra se cada banco
está acessível — se algum falhar, verifique o `.env`, o IP autorizado e o SSL
da instância GCP.

> **Pré-requisito de dados:** as instâncias GCP precisam ter sido carregadas via
> [`../etl/load_relational.py`](../etl/load_relational.py) e
> [`../etl/load_graph.py`](../etl/load_graph.py).
