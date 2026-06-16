-- ==============================================================================
-- Q09: Drogas mais frequentes em combinações perigosas
-- ==============================================================================
-- Pergunta: Quais drogas aparecem com mais frequência em combinações
-- perigosas, e quantos efeitos colaterais distintos essas combinações produzem?
--
-- Abordagem: Como a tabela drug_combination_effect armazena pares com
-- a restrição drug_a_id < drug_b_id, usamos UNION ALL para contabilizar
-- a participação de cada droga em ambas as posições (A e B).
-- ==============================================================================

SELECT
    d.stitch_id,
    COALESCE(d.name, d.stitch_id)  AS drug_name,
    COUNT(*)                        AS n_combination_effects,
    COUNT(DISTINCT dce.se_id)       AS n_distinct_side_effects,
    COUNT(DISTINCT dce.partner_id)  AS n_drug_partners
FROM drug d
JOIN (
    SELECT drug_a_id AS drug_id, drug_b_id AS partner_id, se_id
    FROM drug_combination_effect
    UNION ALL
    SELECT drug_b_id AS drug_id, drug_a_id AS partner_id, se_id
    FROM drug_combination_effect
) dce ON d.drug_id = dce.drug_id
GROUP BY d.drug_id, d.stitch_id, d.name
ORDER BY n_combination_effects DESC
LIMIT 10;
