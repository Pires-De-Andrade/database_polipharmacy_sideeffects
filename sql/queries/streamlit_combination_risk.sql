-- ==============================================================================
-- Streamlit: Perfil de risco de uma combinação de medicamentos
-- ==============================================================================
-- Recebe dois drug_ids (já normalizados com a < b pelo backend).
-- Retorna os efeitos colaterais da combinação com nome e categoria.
--
-- Parâmetros psycopg2: %(drug_a_id)s, %(drug_b_id)s
-- Usa: tabelas drug_combination_effect, side_effect
-- ==============================================================================

SELECT
    se.name        AS side_effect_name,
    se.category    AS category,
    se.umls_cui    AS umls_cui
FROM drug_combination_effect dce
JOIN side_effect se ON dce.se_id = se.se_id
WHERE dce.drug_a_id = %(drug_a_id)s
  AND dce.drug_b_id = %(drug_b_id)s
ORDER BY se.name;
