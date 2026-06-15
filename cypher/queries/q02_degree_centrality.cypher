// ==============================================================================
// Q02: Degree Centrality — Top 20 drogas por grau na rede CAUSES_COMBINED
// ==============================================================================
// Relevância: O grau de um nó Drug na rede de efeitos combinados indica
// com quantas outras drogas ele tem interação documentada. Drogas com alto
// grau são as mais "conectadas" e potencialmente mais problemáticas em
// prescrições de polifarmácia.
// ==============================================================================

MATCH (d:Drug)-[r:CAUSES_COMBINED]-()
WITH d, COUNT(DISTINCT r) AS degree
RETURN
    d.stitch_id AS drug,
    d.name      AS drug_name,
    degree
ORDER BY degree DESC
LIMIT 20;
