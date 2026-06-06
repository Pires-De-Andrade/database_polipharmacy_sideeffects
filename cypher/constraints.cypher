-- ==============================================================================
-- Projeto BD Polifarmácia — Constraints Neo4j (Neo4j 5 Community)
-- ==============================================================================
-- Constraints de unicidade para nós do grafo.
-- Devem ser executados ANTES da carga de dados.
-- ==============================================================================

-- Constraint de unicidade para Drug (stitch_id)
CREATE CONSTRAINT drug_stitch_unique IF NOT EXISTS
FOR (d:Drug) REQUIRE d.stitch_id IS UNIQUE;

-- Constraint de unicidade para Protein (gene_id)
CREATE CONSTRAINT protein_gene_unique IF NOT EXISTS
FOR (p:Protein) REQUIRE p.gene_id IS UNIQUE;

-- Constraint de unicidade para SideEffect (umls_cui)
CREATE CONSTRAINT side_effect_cui_unique IF NOT EXISTS
FOR (s:SideEffect) REQUIRE s.umls_cui IS UNIQUE;
