"""
Lógica de negócio: as consultas analíticas do projeto, expostas como funções.

Cada função encapsula uma query (SQL ou Cypher) versionada do repositório
([sql/queries/], [cypher/queries/]) e retorna um DataFrame pronto para a UI.

As constantes `*_SQL` / `*_CYPHER` ficam expostas para que a página de
comparação dual-paradigma possa exibir o código fonte ao lado do resultado.
"""
from __future__ import annotations

import pandas as pd

from backend.db import run_cypher, run_sql

# ══════════════════════════════════════════════════════════════════════════════
# Pergunta central (notebook): drogas mais frequentes em combinações perigosas
# Resolvida nos DOIS paradigmas para comparação lado a lado.
# ══════════════════════════════════════════════════════════════════════════════
DANGEROUS_DRUGS_SQL = """
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
LIMIT %(limit)s;
"""

DANGEROUS_DRUGS_CYPHER = """
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
LIMIT $limit;
"""


def dangerous_drugs_sql(limit: int = 10) -> pd.DataFrame:
    return run_sql(DANGEROUS_DRUGS_SQL, {"limit": limit})


def dangerous_drugs_cypher(limit: int = 10) -> pd.DataFrame:
    return run_cypher(DANGEROUS_DRUGS_CYPHER, {"limit": limit})


# ══════════════════════════════════════════════════════════════════════════════
# Explorador analítico — PostgreSQL
# ══════════════════════════════════════════════════════════════════════════════
HUB_DRUGS_SQL = """
SELECT d.stitch_id, d.name, COUNT(dpt.protein_id) AS n_targets
FROM drug d
JOIN drug_protein_target dpt ON d.drug_id = dpt.drug_id
GROUP BY d.drug_id, d.stitch_id, d.name
ORDER BY n_targets DESC
LIMIT %(limit)s;
"""

TOP_SIDE_EFFECTS_SQL = """
SELECT se.umls_cui, se.name AS side_effect_name, se.category, COUNT(*) AS n_pairs
FROM drug_combination_effect dce
JOIN side_effect se ON dce.se_id = se.se_id
GROUP BY se.umls_cui, se.name, se.category
HAVING COUNT(*) > %(min_pairs)s
ORDER BY n_pairs DESC
LIMIT %(limit)s;
"""

EMERGENT_EFFECTS_SQL = """
SELECT se.umls_cui, se.name AS side_effect_name, se.category,
       COUNT(*) AS n_emergent_pairs
FROM drug_combination_effect dce
JOIN side_effect se ON dce.se_id = se.se_id
WHERE NOT EXISTS (
    SELECT 1 FROM drug_mono_effect dme
    WHERE dme.drug_id = dce.drug_a_id AND dme.se_id = dce.se_id
)
AND NOT EXISTS (
    SELECT 1 FROM drug_mono_effect dme
    WHERE dme.drug_id = dce.drug_b_id AND dme.se_id = dce.se_id
)
GROUP BY se.umls_cui, se.name, se.category
ORDER BY n_emergent_pairs DESC
LIMIT %(limit)s;
"""

DANGEROUS_PAIRS_SQL = """
SELECT da.stitch_id AS drug_a, da.name AS drug_a_name,
       db.stitch_id AS drug_b, db.name AS drug_b_name,
       COUNT(dce.se_id) AS n_side_effects
FROM drug_combination_effect dce
JOIN drug da ON dce.drug_a_id = da.drug_id
JOIN drug db ON dce.drug_b_id = db.drug_id
GROUP BY da.stitch_id, da.name, db.stitch_id, db.name
ORDER BY n_side_effects DESC
LIMIT %(limit)s;
"""

CATEGORY_ANALYSIS_SQL = """
SELECT se.category,
       COUNT(DISTINCT se.se_id)  AS n_effects_in_category,
       COUNT(DISTINCT dce.se_id) AS n_in_combinations,
       COUNT(DISTINCT dme.se_id) AS n_in_mono
FROM side_effect se
LEFT JOIN drug_combination_effect dce ON se.se_id = dce.se_id
LEFT JOIN drug_mono_effect dme ON se.se_id = dme.se_id
WHERE se.category IS NOT NULL
GROUP BY se.category
ORDER BY n_in_combinations DESC;
"""

DRUG_RISK_PROFILE_SQL = """
SELECT 'MONO' AS effect_type, d.stitch_id AS drug, NULL AS partner_drug,
       se.umls_cui, se.name AS side_effect_name, se.category
FROM drug d
JOIN drug_mono_effect dme ON d.drug_id = dme.drug_id
JOIN side_effect se ON dme.se_id = se.se_id
WHERE d.stitch_id = %(stitch)s
UNION ALL
SELECT 'COMBO', da.stitch_id, db.stitch_id, se.umls_cui, se.name, se.category
FROM drug_combination_effect dce
JOIN drug da ON dce.drug_a_id = da.drug_id
JOIN drug db ON dce.drug_b_id = db.drug_id
JOIN side_effect se ON dce.se_id = se.se_id
WHERE da.stitch_id = %(stitch)s
UNION ALL
SELECT 'COMBO', db.stitch_id, da.stitch_id, se.umls_cui, se.name, se.category
FROM drug_combination_effect dce
JOIN drug da ON dce.drug_a_id = da.drug_id
JOIN drug db ON dce.drug_b_id = db.drug_id
JOIN side_effect se ON dce.se_id = se.se_id
WHERE db.stitch_id = %(stitch)s
ORDER BY effect_type, side_effect_name;
"""

DRUG_LIST_SQL = """
SELECT stitch_id, COALESCE(name, stitch_id) AS label
FROM drug
ORDER BY stitch_id
LIMIT %(limit)s;
"""


def hub_drugs(limit: int = 15) -> pd.DataFrame:
    return run_sql(HUB_DRUGS_SQL, {"limit": limit})


def top_side_effects(min_pairs: int = 500, limit: int = 30) -> pd.DataFrame:
    return run_sql(TOP_SIDE_EFFECTS_SQL, {"min_pairs": min_pairs, "limit": limit})


def emergent_effects(limit: int = 30) -> pd.DataFrame:
    return run_sql(EMERGENT_EFFECTS_SQL, {"limit": limit})


def dangerous_pairs(limit: int = 20) -> pd.DataFrame:
    return run_sql(DANGEROUS_PAIRS_SQL, {"limit": limit})


def category_analysis() -> pd.DataFrame:
    return run_sql(CATEGORY_ANALYSIS_SQL)


def drug_risk_profile(stitch_id: str) -> pd.DataFrame:
    return run_sql(DRUG_RISK_PROFILE_SQL, {"stitch": stitch_id})


def drug_list(limit: int = 2000) -> pd.DataFrame:
    return run_sql(DRUG_LIST_SQL, {"limit": limit})


# ══════════════════════════════════════════════════════════════════════════════
# Explorador analítico / grafo — Neo4j
# ══════════════════════════════════════════════════════════════════════════════
DEGREE_CENTRALITY_CYPHER = """
MATCH (d:Drug)-[r:CAUSES_COMBINED]-()
WITH d, COUNT(DISTINCT r) AS degree
RETURN d.stitch_id AS drug, d.name AS drug_name, degree
ORDER BY degree DESC
LIMIT $limit;
"""

PROTEIN_HUB_CYPHER = """
MATCH (p:Protein)-[:INTERACTS_WITH]-(neighbor:Protein)
WITH p, COUNT(DISTINCT neighbor) AS ppi_degree
WHERE ppi_degree > $min_ppi
MATCH (d:Drug)-[:TARGETS]->(p)
WITH p, ppi_degree, COUNT(DISTINCT d) AS n_drugs_targeting
WHERE n_drugs_targeting >= $min_drugs
RETURN p.gene_id AS protein, p.name AS protein_name,
       ppi_degree AS ppi_connections, n_drugs_targeting AS drugs_targeting
ORDER BY ppi_degree * n_drugs_targeting DESC
LIMIT $limit;
"""

SHARED_PROTEINS_CYPHER = """
MATCH (d1:Drug {stitch_id: $drug_a})-[:TARGETS]->(p:Protein)<-[:TARGETS]-(d2:Drug {stitch_id: $drug_b})
RETURN d1.stitch_id AS drug_1, d2.stitch_id AS drug_2,
       p.gene_id AS shared_protein, p.name AS protein_name
ORDER BY p.gene_id;
"""

SHORTEST_PATH_CYPHER = """
MATCH path = shortestPath(
    (d1:Drug {stitch_id: $drug_a})-[:TARGETS|INTERACTS_WITH*..4]-(d2:Drug {stitch_id: $drug_b})
)
RETURN
    [n IN nodes(path) |
        CASE
            WHEN 'Drug' IN labels(n) THEN 'Drug:' + n.stitch_id
            WHEN 'Protein' IN labels(n) THEN 'Protein:' + toString(n.gene_id)
            ELSE toString(n)
        END
    ] AS path_nodes,
    length(path) AS path_length,
    [r IN relationships(path) | type(r)] AS edge_types;
"""

# Subgrafo das top-N drogas mais conectadas, para visualização (modelo do notebook)
TOP_DRUGS_SUBGRAPH_CYPHER = """
MATCH (d:Drug)-[r:CAUSES_COMBINED]-(other:Drug)
WITH d, count(r) AS freq
ORDER BY freq DESC LIMIT $top_drugs
MATCH (d)-[r:CAUSES_COMBINED]-(other:Drug)
RETURN d.stitch_id AS d1_id, coalesce(d.name, d.stitch_id) AS d1_name,
       other.stitch_id AS d2_id, coalesce(other.name, other.stitch_id) AS d2_name,
       r.se_name AS effect_name
LIMIT $edge_limit;
"""


def degree_centrality(limit: int = 20) -> pd.DataFrame:
    return run_cypher(DEGREE_CENTRALITY_CYPHER, {"limit": limit})


def protein_hubs(min_ppi: int = 10, min_drugs: int = 3, limit: int = 20) -> pd.DataFrame:
    return run_cypher(
        PROTEIN_HUB_CYPHER,
        {"min_ppi": min_ppi, "min_drugs": min_drugs, "limit": limit},
    )


def shared_proteins(drug_a: str, drug_b: str) -> pd.DataFrame:
    return run_cypher(SHARED_PROTEINS_CYPHER, {"drug_a": drug_a, "drug_b": drug_b})


def shortest_path(drug_a: str, drug_b: str) -> pd.DataFrame:
    return run_cypher(SHORTEST_PATH_CYPHER, {"drug_a": drug_a, "drug_b": drug_b})


def top_drugs_subgraph(top_drugs: int = 3, edge_limit: int = 250) -> pd.DataFrame:
    return run_cypher(
        TOP_DRUGS_SUBGRAPH_CYPHER,
        {"top_drugs": top_drugs, "edge_limit": edge_limit},
    )
