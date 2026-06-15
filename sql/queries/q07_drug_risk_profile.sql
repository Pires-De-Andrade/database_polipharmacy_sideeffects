-- ==============================================================================
-- Q07: Perfil de risco de uma droga específica
-- ==============================================================================
-- Relevância: Para uma droga específica, retorna todos os seus efeitos
-- colaterais individuais e todos os efeitos de combinações onde ela participa.
-- Essencial para análise clínica: dado um fármaco que o paciente já usa,
-- quais riscos existem ao adicionar outro medicamento?
--
-- Parâmetro: substituir 'CID000002173' pelo stitch_id desejado.
--
-- Usa: tabelas drug, drug_mono_effect, drug_combination_effect, side_effect
-- Índice utilizado: PKs, idx_drug_combo_effect_drug_b
-- ==============================================================================

-- Parte 1: Efeitos individuais da droga
SELECT
    'MONO' AS effect_type,
    d.stitch_id AS drug,
    NULL AS partner_drug,
    se.umls_cui,
    se.name AS side_effect_name,
    se.category
FROM drug d
JOIN drug_mono_effect dme ON d.drug_id = dme.drug_id
JOIN side_effect se ON dme.se_id = se.se_id
WHERE d.stitch_id = 'CID000002173'

UNION ALL

-- Parte 2: Efeitos em combinação (droga na posição A)
SELECT
    'COMBO' AS effect_type,
    da.stitch_id AS drug,
    db.stitch_id AS partner_drug,
    se.umls_cui,
    se.name AS side_effect_name,
    se.category
FROM drug_combination_effect dce
JOIN drug da ON dce.drug_a_id = da.drug_id
JOIN drug db ON dce.drug_b_id = db.drug_id
JOIN side_effect se ON dce.se_id = se.se_id
WHERE da.stitch_id = 'CID000002173'

UNION ALL

-- Parte 3: Efeitos em combinação (droga na posição B)
SELECT
    'COMBO' AS effect_type,
    db.stitch_id AS drug,
    da.stitch_id AS partner_drug,
    se.umls_cui,
    se.name AS side_effect_name,
    se.category
FROM drug_combination_effect dce
JOIN drug da ON dce.drug_a_id = da.drug_id
JOIN drug db ON dce.drug_b_id = db.drug_id
JOIN side_effect se ON dce.se_id = se.se_id
WHERE db.stitch_id = 'CID000002173'

ORDER BY effect_type, side_effect_name;
