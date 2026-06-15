// ==============================================================================
// Q03: Caminho mais curto entre duas drogas via rede proteica
// ==============================================================================
// Relevância: Encontra o caminho mais curto entre duas drogas através da
// rede de alvos proteicos (TARGETS) e interações proteína-proteína
// (INTERACTS_WITH). Caminhos curtos sugerem proximidade farmacológica
// e maior potencial de interação.
//
// Limite de 4 saltos para evitar explosão combinatória na rede PPI (~719k arestas).
// Parâmetros: substituir os stitch_ids pelas drogas de interesse.
// ==============================================================================

MATCH path = shortestPath(
    (d1:Drug {stitch_id: 'CID000002173'})-[:TARGETS|INTERACTS_WITH*..4]-(d2:Drug {stitch_id: 'CID000003345'})
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
