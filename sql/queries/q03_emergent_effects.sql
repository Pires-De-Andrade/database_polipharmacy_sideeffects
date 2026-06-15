-- ==============================================================================
-- Q03: Efeitos emergentes — aparecem em combinação mas NÃO individualmente
-- ==============================================================================
-- Relevância: Este é o cenário mais perigoso da polifarmácia: efeitos colaterais
-- que NÃO são observados quando cada droga é usada sozinha, mas que emergem
-- quando as drogas são combinadas. Estes são os efeitos verdadeiramente
-- "emergentes" e imprevisíveis.
--
-- Estratégia: para cada par (drug_a, drug_b, se_id) em drug_combination_effect,
-- verificar se NÃO existe (drug_a, se_id) nem (drug_b, se_id) em drug_mono_effect.
--
-- Usa: tabelas drug_combination_effect, drug_mono_effect, side_effect
-- Índice utilizado: PKs de drug_mono_effect e drug_combination_effect
-- ==============================================================================

SELECT
    se.umls_cui,
    se.name        AS side_effect_name,
    se.category,
    COUNT(*)       AS n_emergent_pairs
FROM drug_combination_effect dce
JOIN side_effect se ON dce.se_id = se.se_id
WHERE NOT EXISTS (
    SELECT 1 FROM drug_mono_effect dme
    WHERE dme.drug_id = dce.drug_a_id AND dme.se_id = dce.se_id
)
AND NOT EXISTS (
    SELECT 1 FROM drug_mono_effect dme
    WHERE dme.drug_id = dce.drug_b_id AND dme.se_id = dce.se_id
)
GROUP BY se.umls_cui, se.name, se.category
ORDER BY n_emergent_pairs DESC
LIMIT 30;
