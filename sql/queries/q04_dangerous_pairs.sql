-- ==============================================================================
-- Q04: Pares de drogas mais perigosos — maior número de efeitos combinados
-- ==============================================================================
-- Relevância: Pares com muitos efeitos colaterais combinados representam as
-- combinações mais arriscadas do ponto de vista clínico. Esta query ajuda a
-- identificar pares que deveriam ser evitados ou monitorados com atenção.
--
-- Usa: tabelas drug_combination_effect, drug
-- Índice utilizado: PK de drug_combination_effect (drug_a_id, drug_b_id, se_id)
-- ==============================================================================

SELECT
    da.stitch_id   AS drug_a,
    da.name        AS drug_a_name,
    db.stitch_id   AS drug_b,
    db.name        AS drug_b_name,
    COUNT(dce.se_id) AS n_side_effects
FROM drug_combination_effect dce
JOIN drug da ON dce.drug_a_id = da.drug_id
JOIN drug db ON dce.drug_b_id = db.drug_id
GROUP BY da.stitch_id, da.name, db.stitch_id, db.name
ORDER BY n_side_effects DESC
LIMIT 20;
