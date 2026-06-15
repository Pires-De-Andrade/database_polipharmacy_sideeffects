-- ==============================================================================
-- Q06: Distribuição de efeitos colaterais por categoria
-- ==============================================================================
-- Relevância: Analisa como os efeitos colaterais se distribuem entre as
-- categorias de doença (Disease Class). Permite entender quais sistemas
-- corporais são mais afetados pela polifarmácia (ex: sistema nervoso,
-- gastrointestinal, cardiovascular).
--
-- Calcula: total de efeitos na categoria, quantos aparecem em combinações,
-- quantos aparecem individualmente, e quantos são exclusivos de combinações.
--
-- Usa: tabelas side_effect, drug_combination_effect, drug_mono_effect
-- Índice utilizado: idx_side_effect_category
-- ==============================================================================

SELECT
    se.category,
    COUNT(DISTINCT se.se_id)   AS n_effects_in_category,
    COUNT(DISTINCT dce.se_id)  AS n_in_combinations,
    COUNT(DISTINCT dme.se_id)  AS n_in_mono,
    COUNT(DISTINCT dce.se_id) - COUNT(DISTINCT CASE
        WHEN dme.se_id IS NOT NULL THEN dce.se_id
    END) AS n_combo_only
FROM side_effect se
LEFT JOIN drug_combination_effect dce ON se.se_id = dce.se_id
LEFT JOIN drug_mono_effect dme ON se.se_id = dme.se_id
WHERE se.category IS NOT NULL
GROUP BY se.category
ORDER BY n_in_combinations DESC;
