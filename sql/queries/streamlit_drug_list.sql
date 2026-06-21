-- ==============================================================================
-- Streamlit: Lista de medicamentos para os dropdowns
-- ==============================================================================
-- Retorna todos os medicamentos com label legível (nome ou stitch_id).
-- Usado pelo componente selector.py com cache TTL=3600.
--
-- Usa: tabela drug
-- ==============================================================================

SELECT
    drug_id,
    stitch_id,
    COALESCE(name, stitch_id) AS label
FROM drug
ORDER BY label;
