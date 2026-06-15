// ==============================================================================
// Q06: Proteínas hub na rede PPI que são alvo de pelo menos 3 drogas
// ==============================================================================
// Relevância: Proteínas com alto grau na rede PPI E que são alvo de
// múltiplas drogas representam pontos de vulnerabilidade do sistema biológico.
// Perturbações nesses "hubs farmacológicos" por múltiplas drogas simultâneas
// podem amplificar efeitos colaterais de forma desproporcional.
//
// A query combina centralidade de grau na rede PPI com o número de drogas
// que têm essa proteína como alvo.
// ==============================================================================

MATCH (p:Protein)-[:INTERACTS_WITH]-(neighbor:Protein)
WITH p, COUNT(DISTINCT neighbor) AS ppi_degree
WHERE ppi_degree > 10

MATCH (d:Drug)-[:TARGETS]->(p)
WITH p, ppi_degree, COUNT(DISTINCT d) AS n_drugs_targeting
WHERE n_drugs_targeting >= 3

RETURN
    p.gene_id    AS protein,
    p.name       AS protein_name,
    ppi_degree   AS ppi_connections,
    n_drugs_targeting AS drugs_targeting

ORDER BY ppi_degree * n_drugs_targeting DESC
LIMIT 20;
