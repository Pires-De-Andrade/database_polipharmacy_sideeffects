-- ==============================================================================
-- Projeto BD Polifarmácia — Índices (PostgreSQL 16)
-- ==============================================================================
-- Estratégia de indexação focada nas colunas de JOIN mais frequentes
-- nas tabelas de relacionamento. As PKs já criam índices implícitos.
--
-- Nota: Índices nas colunas FK aceleram JOINs e DELETE cascading.
-- O PostgreSQL NÃO cria índices automáticos em colunas FK (ao contrário da PK).
-- ==============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- drug_protein_target
-- ─────────────────────────────────────────────────────────────────────────────
-- PK (drug_id, protein_id) já cria índice composto com drug_id como prefixo.
-- Precisamos de índice separado em protein_id para buscas reversas:
-- "quais drogas têm a proteína X como alvo?"
CREATE INDEX idx_drug_protein_target_protein
    ON drug_protein_target (protein_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- protein_interaction
-- ─────────────────────────────────────────────────────────────────────────────
-- PK (protein_a_id, protein_b_id) indexa buscas por protein_a_id.
-- Índice separado em protein_b_id para busca reversa:
-- "quais proteínas interagem com a proteína X?" (quando X está na posição B)
CREATE INDEX idx_protein_interaction_b
    ON protein_interaction (protein_b_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- drug_mono_effect
-- ─────────────────────────────────────────────────────────────────────────────
-- PK (drug_id, se_id) indexa buscas por drug_id.
-- Índice em se_id para busca reversa:
-- "quais drogas causam o efeito colateral X individualmente?"
CREATE INDEX idx_drug_mono_effect_se
    ON drug_mono_effect (se_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- drug_combination_effect
-- ─────────────────────────────────────────────────────────────────────────────
-- PK (drug_a_id, drug_b_id, se_id) indexa buscas pelo prefixo drug_a_id.
-- Índices adicionais para padrões de consulta frequentes:

-- Busca por drug_b_id: "pares que incluem a droga X na posição B"
CREATE INDEX idx_drug_combo_effect_drug_b
    ON drug_combination_effect (drug_b_id);

-- Busca por se_id: "quais pares de drogas causam o efeito X?"
CREATE INDEX idx_drug_combo_effect_se
    ON drug_combination_effect (se_id);

-- Índice composto (drug_b_id, se_id) para consultas que filtram por ambos
-- (ex: "pares com droga X que causam efeito Y")
CREATE INDEX idx_drug_combo_effect_drug_b_se
    ON drug_combination_effect (drug_b_id, se_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- side_effect — busca por categoria
-- ─────────────────────────────────────────────────────────────────────────────
-- Facilita agrupamento e filtragem por Disease Class
CREATE INDEX idx_side_effect_category
    ON side_effect (category);

-- ─────────────────────────────────────────────────────────────────────────────
-- Índices para lookup pelas chaves naturais (usados durante ETL)
-- ─────────────────────────────────────────────────────────────────────────────
-- Esses já são cobertos pelas constraints UNIQUE (que criam índices), mas
-- listamos explicitamente para documentação:
-- • drug.stitch_id          → idx_drug_stitch_id (via UNIQUE)
-- • protein.gene_id         → idx_protein_gene_id (via UNIQUE)
-- • side_effect.umls_cui    → idx_side_effect_umls_cui (via UNIQUE)
