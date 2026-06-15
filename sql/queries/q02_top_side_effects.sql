-- ==============================================================================
-- Q02: Top efeitos colaterais mais frequentes em combinações (> 500 pares)
-- ==============================================================================
-- Relevância: Identifica os efeitos colaterais que aparecem com mais frequência
-- quando drogas são combinadas. Efeitos muito comuns podem indicar mecanismos
-- farmacológicos compartilhados entre grandes classes de medicamentos.
--
-- Filtro: apenas efeitos que aparecem em mais de 500 pares distintos.
-- Usa: tabelas drug_combination_effect, side_effect
-- Índice utilizado: idx_drug_combo_effect_se (se_id)
-- ==============================================================================

SELECT
    se.umls_cui,
    se.name       AS side_effect_name,
    se.category,
    COUNT(*)      AS n_pairs
FROM drug_combination_effect dce
JOIN side_effect se ON dce.se_id = se.se_id
GROUP BY se.umls_cui, se.name, se.category
HAVING COUNT(*) > 500
ORDER BY n_pairs DESC;
