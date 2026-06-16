// ==============================================================================
// Q07: Drogas mais frequentes em combinações perigosas (Cypher)
// ==============================================================================
// Pergunta: Quais drogas aparecem com mais frequência em combinações
// perigosas, e quantos efeitos colaterais distintos essas combinações produzem?
//
// Abordagem: No grafo, CAUSES_COMBINED conecta Drug→Drug com o efeito
// como propriedade da aresta. Usamos o padrão não-direcional (sem seta)
// para capturar a participação da droga em ambas as direções.
// ==============================================================================

MATCH (d:Drug)-[r:CAUSES_COMBINED]-(other:Drug)
WITH d,
     COUNT(r)                   AS n_combination_effects,
     COUNT(DISTINCT r.se_id)    AS n_distinct_side_effects,
     COUNT(DISTINCT other)      AS n_drug_partners
RETURN d.stitch_id              AS stitch_id,
       n_combination_effects,
       n_distinct_side_effects,
       n_drug_partners
ORDER BY n_combination_effects DESC
LIMIT 10;
