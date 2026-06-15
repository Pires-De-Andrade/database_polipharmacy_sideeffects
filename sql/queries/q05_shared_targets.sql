-- ==============================================================================
-- Q05: Proteínas-alvo compartilhadas entre pares de drogas com efeito combinado
-- ==============================================================================
-- Relevância: Uma hipótese central do artigo Zitnik et al. (2018) é que efeitos
-- colaterais de polifarmácia estão correlacionados com alvos proteicos
-- compartilhados entre as drogas. Esta query verifica essa hipótese contando
-- quantas proteínas-alvo os pares de drogas com efeitos combinados compartilham.
--
-- Pares com muitas proteínas compartilhadas podem explicar mecanismos moleculares
-- subjacentes aos efeitos colaterais emergentes.
--
-- Usa: tabelas drug_combination_effect, drug_protein_target
-- Índice utilizado: idx_drug_protein_target_protein (protein_id)
-- ==============================================================================

SELECT
    da.stitch_id    AS drug_a,
    db.stitch_id    AS drug_b,
    COUNT(DISTINCT dce.se_id)   AS n_combo_effects,
    COUNT(DISTINCT shared.protein_id) AS n_shared_targets
FROM (
    -- Pares distintos de drogas com efeitos combinados
    SELECT DISTINCT drug_a_id, drug_b_id
    FROM drug_combination_effect
) pairs
JOIN drug da ON pairs.drug_a_id = da.drug_id
JOIN drug db ON pairs.drug_b_id = db.drug_id
JOIN drug_combination_effect dce
    ON dce.drug_a_id = pairs.drug_a_id AND dce.drug_b_id = pairs.drug_b_id
LEFT JOIN (
    -- Proteínas que ambas as drogas do par têm como alvo
    SELECT t1.drug_id AS drug_a_id, t2.drug_id AS drug_b_id, t1.protein_id
    FROM drug_protein_target t1
    JOIN drug_protein_target t2 ON t1.protein_id = t2.protein_id
    WHERE t1.drug_id < t2.drug_id
) shared
    ON shared.drug_a_id = pairs.drug_a_id AND shared.drug_b_id = pairs.drug_b_id
GROUP BY da.stitch_id, db.stitch_id
HAVING COUNT(DISTINCT shared.protein_id) > 0
ORDER BY n_shared_targets DESC, n_combo_effects DESC
LIMIT 20;
