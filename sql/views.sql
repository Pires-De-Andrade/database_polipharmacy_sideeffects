-- ==============================================================================
-- Projeto BD Polifarmácia — Views (PostgreSQL 16)
-- ==============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- vw_drug_risk_summary
-- ─────────────────────────────────────────────────────────────────────────────
-- Para cada droga, agrega indicadores de risco:
--   • n_mono_effects: quantos efeitos colaterais individuais conhecidos
--   • n_combination_effects: quantos efeitos em combinações com outras drogas
--   • n_distinct_partners: com quantas drogas distintas forma combinações
--   • n_target_proteins: quantas proteínas são alvo terapêutico
--
-- Uso: SELECT * FROM vw_drug_risk_summary ORDER BY n_combination_effects DESC;
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_drug_risk_summary AS
SELECT
    d.drug_id,
    d.stitch_id,
    d.name,
    COALESCE(mono.n_mono_effects, 0)         AS n_mono_effects,
    COALESCE(combo.n_combination_effects, 0) AS n_combination_effects,
    COALESCE(combo.n_distinct_partners, 0)   AS n_distinct_partners,
    COALESCE(targets.n_target_proteins, 0)   AS n_target_proteins
FROM drug d
LEFT JOIN (
    SELECT drug_id, COUNT(*) AS n_mono_effects
    FROM drug_mono_effect
    GROUP BY drug_id
) mono ON d.drug_id = mono.drug_id
LEFT JOIN (
    -- Combinações onde a droga aparece na posição A ou B
    SELECT
        drug_id,
        COUNT(*)                  AS n_combination_effects,
        COUNT(DISTINCT partner_id) AS n_distinct_partners
    FROM (
        SELECT drug_a_id AS drug_id, drug_b_id AS partner_id, se_id
        FROM drug_combination_effect
        UNION ALL
        SELECT drug_b_id AS drug_id, drug_a_id AS partner_id, se_id
        FROM drug_combination_effect
    ) all_combos
    GROUP BY drug_id
) combo ON d.drug_id = combo.drug_id
LEFT JOIN (
    SELECT drug_id, COUNT(*) AS n_target_proteins
    FROM drug_protein_target
    GROUP BY drug_id
) targets ON d.drug_id = targets.drug_id;

COMMENT ON VIEW vw_drug_risk_summary IS
    'Resumo de risco por droga: efeitos mono, combo, parceiros e alvos proteicos.';


-- ─────────────────────────────────────────────────────────────────────────────
-- vw_top_dangerous_combinations
-- ─────────────────────────────────────────────────────────────────────────────
-- Join entre drug_combination_effect e drug, retornando os STITCH IDs
-- de ambos os fármacos, o nome do efeito colateral, sua categoria e
-- o n_reports (quando disponível).
--
-- Filtrável por efeito via WHERE:
--   SELECT * FROM vw_top_dangerous_combinations
--   WHERE side_effect_name ILIKE '%cardiac%';
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_top_dangerous_combinations AS
SELECT
    da.stitch_id    AS drug_a_stitch,
    da.name         AS drug_a_name,
    db.stitch_id    AS drug_b_stitch,
    db.name         AS drug_b_name,
    se.umls_cui,
    se.name         AS side_effect_name,
    se.category     AS side_effect_category,
    dce.n_reports
FROM drug_combination_effect dce
JOIN drug da         ON dce.drug_a_id = da.drug_id
JOIN drug db         ON dce.drug_b_id = db.drug_id
JOIN side_effect se  ON dce.se_id = se.se_id;

COMMENT ON VIEW vw_top_dangerous_combinations IS
    'Combinações de drogas com efeitos colaterais — filtrável por efeito ou categoria.';
