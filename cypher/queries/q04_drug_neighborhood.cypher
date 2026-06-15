// ==============================================================================
// Q04: Vizinhança de 1 e 2 saltos de uma droga na rede combinada
// ==============================================================================
// Relevância: Mostra a vizinhança local de uma droga considerando todas
// as relações (TARGETS, CAUSES_COMBINED, HAS_MONO_EFFECT). Útil para
// exploração visual e para entender o "contexto farmacológico" de uma droga.
//
// Retorna nós vizinhos de 1o e 2o grau com o tipo de relação.
// Parâmetro: substituir o stitch_id pela droga de interesse.
// ==============================================================================

// Vizinhança de 1 salto
MATCH (d:Drug {stitch_id: 'CID000002173'})-[r]-(neighbor)
RETURN
    d.stitch_id        AS source,
    type(r)            AS relationship,
    labels(neighbor)[0] AS neighbor_type,
    CASE
        WHEN 'Drug' IN labels(neighbor) THEN neighbor.stitch_id
        WHEN 'Protein' IN labels(neighbor) THEN toString(neighbor.gene_id)
        WHEN 'SideEffect' IN labels(neighbor) THEN neighbor.name
    END AS neighbor_id,
    1 AS hop
ORDER BY relationship, neighbor_type

UNION

// Vizinhança de 2 saltos (via proteínas-alvo)
MATCH (d:Drug {stitch_id: 'CID000002173'})-[:TARGETS]->(p:Protein)-[:INTERACTS_WITH]-(p2:Protein)
RETURN
    d.stitch_id             AS source,
    'TARGETS→INTERACTS_WITH' AS relationship,
    'Protein'               AS neighbor_type,
    toString(p2.gene_id)    AS neighbor_id,
    2 AS hop
LIMIT 50;
