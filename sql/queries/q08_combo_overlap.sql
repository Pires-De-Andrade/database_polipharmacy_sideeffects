-- ==============================================================================
-- Q08: Co-ocorrência de efeitos colaterais em combinações (> 300 pares)
-- ==============================================================================
-- Relevância: Detecta pares de efeitos colaterais que frequentemente co-ocorrem
-- no mesmo par de drogas. Isso pode indicar que os dois efeitos compartilham
-- um mecanismo biológico comum (pathway metabólico, receptor, etc.) ou que
-- um efeito é consequência do outro.
--
-- Filtro: apenas pares que co-ocorrem em mais de 300 combinações para
-- reduzir ruído e focar em padrões estatisticamente relevantes.
--
-- ATENÇÃO: esta query é computacionalmente pesada pois faz um self-join na
-- tabela de ~4.65M linhas. Pode levar alguns minutos no dataset completo.
--
-- Usa: tabela drug_combination_effect, side_effect
-- Índice utilizado: PK de drug_combination_effect
-- ==============================================================================

SELECT
    se1.name       AS effect_1,
    se2.name       AS effect_2,
    se1.category   AS category_1,
    se2.category   AS category_2,
    COUNT(*)       AS n_shared_pairs
FROM drug_combination_effect dce1
JOIN drug_combination_effect dce2
    ON  dce1.drug_a_id = dce2.drug_a_id
    AND dce1.drug_b_id = dce2.drug_b_id
    AND dce1.se_id < dce2.se_id           -- evitar duplicatas e auto-par
JOIN side_effect se1 ON dce1.se_id = se1.se_id
JOIN side_effect se2 ON dce2.se_id = se2.se_id
GROUP BY se1.name, se2.name, se1.category, se2.category
HAVING COUNT(*) > 300
ORDER BY n_shared_pairs DESC
LIMIT 30;
