// ==============================================================================
// Streamlit: Contexto molecular de um par de medicamentos
// ==============================================================================
// Retorna os nós (Drug, Protein) e arestas (TARGETS, INTERACTS_WITH) que
// conectam dois medicamentos na rede molecular. Usado para construir o
// grafo interactivo pyvis na Tab 2.
//
// Parâmetros Neo4j: $stitch_a, $stitch_b
// ==============================================================================

// 1. Proteínas-alvo de cada medicamento
MATCH (da:Drug {stitch_id: $stitch_a})
OPTIONAL MATCH (da)-[:TARGETS]->(pa:Protein)
WITH da, COLLECT(DISTINCT pa) AS proteins_a

MATCH (db:Drug {stitch_id: $stitch_b})
OPTIONAL MATCH (db)-[:TARGETS]->(pb:Protein)
WITH da, db, proteins_a, COLLECT(DISTINCT pb) AS proteins_b

// 2. Calcular partilhadas vs exclusivas
WITH da, db, proteins_a, proteins_b,
     [p IN proteins_a WHERE p IN proteins_b] AS shared,
     [p IN proteins_a WHERE NOT p IN proteins_b] AS exclusive_a,
     [p IN proteins_b WHERE NOT p IN proteins_a] AS exclusive_b

// 3. Retornar tudo como listas para construção do grafo no Python
RETURN
    da.stitch_id AS drug_a_stitch,
    COALESCE(da.name, da.stitch_id) AS drug_a_name,
    db.stitch_id AS drug_b_stitch,
    COALESCE(db.name, db.stitch_id) AS drug_b_name,
    [p IN shared | {gene_id: p.gene_id, name: COALESCE(p.name, toString(p.gene_id))}] AS shared_proteins,
    [p IN exclusive_a | {gene_id: p.gene_id, name: COALESCE(p.name, toString(p.gene_id))}] AS exclusive_a_proteins,
    [p IN exclusive_b | {gene_id: p.gene_id, name: COALESCE(p.name, toString(p.gene_id))}] AS exclusive_b_proteins;
