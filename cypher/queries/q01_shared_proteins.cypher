// ==============================================================================
// Q01: Proteínas compartilhadas entre duas drogas específicas
// ==============================================================================
// Relevância: Identifica os alvos proteicos que duas drogas têm em comum.
// Proteínas compartilhadas podem explicar interações farmacodinâmicas
// e efeitos colaterais emergentes na combinação.
//
// Parâmetros: substituir os stitch_ids pelas drogas de interesse.
// ==============================================================================

MATCH (d1:Drug {stitch_id: 'CID000002173'})-[:TARGETS]->(p:Protein)<-[:TARGETS]-(d2:Drug {stitch_id: 'CID000003345'})
RETURN
    d1.stitch_id AS drug_1,
    d2.stitch_id AS drug_2,
    p.gene_id    AS shared_protein,
    p.name       AS protein_name
ORDER BY p.gene_id;
