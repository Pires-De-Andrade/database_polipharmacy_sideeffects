-- ==============================================================================
-- Streamlit: Filtro dinâmico de pares válidos
-- ==============================================================================
-- Recebe um drug_id e retorna todos os medicamentos que têm uma 
-- interacção registada com ele no dataset (drug_combination_effect).
--
-- Parâmetros psycopg2: %(drug_id)s
-- ==============================================================================

SELECT DISTINCT drug_b_id AS drug_id
FROM drug_combination_effect
WHERE drug_a_id = %(drug_id)s

UNION

SELECT DISTINCT drug_a_id AS drug_id
FROM drug_combination_effect
WHERE drug_b_id = %(drug_id)s;
