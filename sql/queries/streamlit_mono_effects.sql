-- ==============================================================================
-- Streamlit: Efeitos colaterais mono (medicamento individual)
-- ==============================================================================
-- Retorna os efeitos colaterais conhecidos de um medicamento usado sozinho.
-- Serve de baseline de risco antes de avaliar a combinação.
--
-- Parâmetros psycopg2: %(drug_id)s
-- Usa: tabelas drug_mono_effect, side_effect
-- ==============================================================================

SELECT
    se.name        AS side_effect_name,
    se.category    AS category,
    se.umls_cui    AS umls_cui
FROM drug_mono_effect dme
JOIN side_effect se ON dme.se_id = se.se_id
WHERE dme.drug_id = %(drug_id)s
ORDER BY se.name;
