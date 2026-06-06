# Esquema do Banco de Dados — Projeto Polifarmácia

## Visão Geral

Este projeto modela efeitos colaterais de polifarmácia (uso simultâneo de múltiplos medicamentos) usando dados do [DECAGON/SNAP Stanford](http://snap.stanford.edu/decagon).

## Modelo Relacional (PostgreSQL 16)

### Diagrama ER

```
┌──────────────┐       ┌───────────────────────┐       ┌──────────────┐
│    Drug      │       │  drug_protein_target   │       │   Protein    │
├──────────────┤       ├───────────────────────┤       ├──────────────┤
│ drug_id (PK) │◄──FK──│ drug_id (PK,FK)       │──FK──►│protein_id(PK)│
│ stitch_id    │       │ protein_id (PK,FK)    │       │ gene_id      │
│ name         │       │ evidence_score        │       │ name         │
└──────┬───────┘       └───────────────────────┘       └──────┬───────┘
       │                                                      │
       │  ┌──────────────────────────────┐                    │
       │  │  drug_combination_effect     │                    │
       │  ├──────────────────────────────┤                    │
       ├──│ drug_a_id (PK,FK)  [a < b]  │                    │
       ├──│ drug_b_id (PK,FK)           │                    │
       │  │ se_id (PK,FK)──────────────►├──┐                 │
       │  │ n_reports                    │  │                 │
       │  └──────────────────────────────┘  │                 │
       │                                    │                 │
       │  ┌──────────────────────────────┐  │                 │
       │  │  drug_mono_effect            │  │                 │
       │  ├──────────────────────────────┤  │                 │
       └──│ drug_id (PK,FK)             │  │  ┌────────────────────────────┐
          │ se_id (PK,FK)───────────────┼──┼─►│      side_effect           │
          │ source                       │  │  ├────────────────────────────┤
          └──────────────────────────────┘  └─►│ se_id (PK)               │
                                               │ umls_cui (UNIQUE)        │
       ┌──────────────────────────────┐        │ name                      │
       │  protein_interaction         │        │ category                  │
       ├──────────────────────────────┤        └────────────────────────────┘
       │ protein_a_id (PK,FK) [a < b]│
       │ protein_b_id (PK,FK)        │
       └──────────────────────────────┘
```

### Tabelas

| Tabela | Descrição | Linhas esperadas |
|--------|-----------|-----------------|
| `drug` | Medicamentos (STITCH ID) | ~640 |
| `protein` | Proteínas/genes (Entrez Gene ID) | ~19.085 |
| `side_effect` | Efeitos colaterais (UMLS CUI) | ~964+ |
| `drug_protein_target` | Droga → proteína-alvo | ~18.596 |
| `protein_interaction` | PPI (simétrica, a < b) | ~719.402 |
| `drug_mono_effect` | Efeitos de droga individual | ~174.977 |
| `drug_combination_effect` | Efeitos de pares (polifarmácia) | ~4.651.131 |

### Decisões de Modelagem

1. **Chaves surrogate (SERIAL)**: Usadas nas entidades principais (`drug`, `protein`, `side_effect`) para independência dos identificadores externos.

2. **Chaves naturais preservadas**: `stitch_id`, `gene_id`, `umls_cui` mantidas como colunas `UNIQUE` para lookups durante ETL.

3. **Simetria normalizada**: Em `protein_interaction` e `drug_combination_effect`, aplicamos `CHECK (a < b)` para armazenar cada par uma única vez.

4. **Campos futuros**: `evidence_score`, `n_reports`, `source` foram incluídos no schema mesmo ausentes dos CSVs, permitindo enriquecimento posterior.

5. **ON DELETE CASCADE**: Aplicado em todas as FKs para simplificar limpeza de dados.

## Modelo de Grafos (Neo4j 5)

### Nós

| Label | Propriedades | Constraint |
|-------|-------------|-----------|
| `:Drug` | `stitch_id`, `name` | `stitch_id` UNIQUE |
| `:Protein` | `gene_id`, `name` | `gene_id` UNIQUE |
| `:SideEffect` | `umls_cui`, `name`, `category` | `umls_cui` UNIQUE |

### Arestas

| Tipo | Origem → Destino | Propriedades |
|------|-------------------|-------------|
| `TARGETS` | Drug → Protein | `evidence_score` |
| `INTERACTS_WITH` | Protein → Protein | — |
| `CAUSES_COMBINED` | Drug → Drug | `se_id`, `se_name`, `n_reports` |
| `HAS_MONO_EFFECT` | Drug → SideEffect | `source` |

## Fontes de Dados

| Arquivo | Colunas | Descrição |
|---------|---------|-----------|
| `bio-decagon-ppi.csv` | Gene 1, Gene 2 | Interações proteína-proteína |
| `bio-decagon-targets.csv` | STITCH, Gene | Droga → proteína-alvo |
| `bio-decagon-combo.csv` | STITCH 1, STITCH 2, Polypharmacy Side Effect, Side Effect Name | Efeitos de pares |
| `bio-decagon-mono.csv` | STITCH, Individual Side Effect, Side Effect Name | Efeitos individuais |
| `bio-decagon-effectcategories.csv` | Side Effect, Side Effect Name, Disease Class | Categorias |
