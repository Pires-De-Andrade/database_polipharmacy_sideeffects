// ==============================================================================
// Q05: Co-ocorrência de efeitos colaterais no mesmo par de drogas
// ==============================================================================
// Relevância: Detecta pares de efeitos colaterais que co-ocorrem como arestas
// CAUSES_COMBINED entre o mesmo par de drogas. Alta co-ocorrência pode indicar
// que os efeitos estão biologicamente relacionados (mesmo pathway, mesmo órgão).
//
// Estratégia: para cada par de drogas com múltiplas arestas CAUSES_COMBINED,
// gerar pares de efeitos e contar co-ocorrências.
// ==============================================================================

MATCH (d1:Drug)-[r1:CAUSES_COMBINED]->(d2:Drug),
      (d1)-[r2:CAUSES_COMBINED]->(d2)
WHERE r1.se_id < r2.se_id
WITH r1.se_name AS effect_1, r2.se_name AS effect_2, COUNT(*) AS n_cooccurrences
WHERE n_cooccurrences > 200
RETURN effect_1, effect_2, n_cooccurrences
ORDER BY n_cooccurrences DESC
LIMIT 25;
