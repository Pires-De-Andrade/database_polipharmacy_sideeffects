-- ==============================================================================
-- Q01: Hub Drugs — Top 15 drogas com mais proteínas-alvo
-- ==============================================================================
-- Relevância: Drogas que interagem com muitas proteínas (hubs farmacológicos)
-- têm maior probabilidade de causar efeitos colaterais inesperados quando
-- combinadas, pois compartilham alvos moleculares com mais fármacos.
--
-- Usa: tabelas drug, drug_protein_target
-- Índice utilizado: PK de drug_protein_target (drug_id, protein_id)
-- ==============================================================================

SELECT
    d.drug_id,
    d.stitch_id,
    d.name,
    COUNT(dpt.protein_id) AS n_targets
FROM drug d
JOIN drug_protein_target dpt ON d.drug_id = dpt.drug_id
GROUP BY d.drug_id, d.stitch_id, d.name
ORDER BY n_targets DESC
LIMIT 15;
