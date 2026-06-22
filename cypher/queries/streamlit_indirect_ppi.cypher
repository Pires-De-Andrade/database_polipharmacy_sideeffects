// ==============================================================================
// Streamlit (EXPERIMENTAL): Interação indirecta via rede PPI
// ==============================================================================
// Mecanismo central do DECAGON: dois medicamentos podem interagir mesmo SEM
// partilharem um alvo directo, desde que os seus alvos estejam ligados na rede
// de interacção proteína-proteína (PPI).
//
// Encontra "pontes" no padrão:
//     (Drug A)-[:TARGETS]->(pa)-[:INTERACTS_WITH]-(pb)<-[:TARGETS]-(Drug B)
// com pa <> pb (alvos partilhados directos são tratados na aba Contexto Molecular).
//
// Parâmetros Neo4j: $stitch_a, $stitch_b
// LIMIT protege contra medicamentos com elevado número de alvos.
// ==============================================================================

MATCH (da:Drug {stitch_id: $stitch_a})-[:TARGETS]->(pa:Protein)
MATCH (db:Drug {stitch_id: $stitch_b})-[:TARGETS]->(pb:Protein)
WHERE pa <> pb AND (pa)-[:INTERACTS_WITH]-(pb)
WITH DISTINCT pa, pb
RETURN
    pa.gene_id                              AS a_gene,
    COALESCE(pa.name, toString(pa.gene_id)) AS a_name,
    pb.gene_id                              AS b_gene,
    COALESCE(pb.name, toString(pb.gene_id)) AS b_name
LIMIT 300;
