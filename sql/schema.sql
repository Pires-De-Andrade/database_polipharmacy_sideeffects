-- ==============================================================================
-- Projeto BD Polifarmácia — DDL (PostgreSQL 16)
-- ==============================================================================
-- Domínio: Modelagem de efeitos colaterais de polifarmácia.
-- Fonte:   Zitnik et al. (2018) — datasets do projeto DECAGON (SNAP Stanford).
--
-- Convenções:
--   • snake_case para todos os identificadores
--   • Chaves primárias surrogate (SERIAL) para entidades principais
--   • Chaves naturais preservadas como colunas UNIQUE (stitch_id, uniprot_id, etc.)
--   • Tabelas de relacionamento usam PKs compostas
--   • Comentários COMMENT ON para documentação inline no catálogo
-- ==============================================================================

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. DRUG — Medicamentos identificados pelo STITCH ID
-- ─────────────────────────────────────────────────────────────────────────────
-- Cada droga possui um identificador STITCH (ex: CID000002173) que é a chave
-- de junção natural nos CSVs do DECAGON. O campo `name` é nullable porque os
-- CSVs não fornecem nomes comerciais diretamente — pode ser enriquecido depois.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE drug (
    drug_id     SERIAL      PRIMARY KEY,
    stitch_id   VARCHAR(20) NOT NULL UNIQUE,
    name        VARCHAR(255)
);

COMMENT ON TABLE  drug             IS 'Medicamentos com identificador STITCH (DECAGON/SNAP).';
COMMENT ON COLUMN drug.stitch_id   IS 'Identificador STITCH composto (ex: CID000002173).';
COMMENT ON COLUMN drug.name        IS 'Nome comercial/genérico (preenchido via enriquecimento).';


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. PROTEIN — Proteínas identificadas pelo Entrez Gene ID
-- ─────────────────────────────────────────────────────────────────────────────
-- O dataset DECAGON usa Entrez Gene IDs (inteiros) como identificadores de
-- genes/proteínas nas interações PPI e nos alvos de drogas.
-- O campo `gene_id` armazena o ID Entrez original como inteiro.
-- O campo `name` é nullable, pode ser enriquecido via APIs (UniProt, NCBI).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE protein (
    protein_id  SERIAL       PRIMARY KEY,
    gene_id     INTEGER      NOT NULL UNIQUE,
    name        VARCHAR(255)
);

COMMENT ON TABLE  protein            IS 'Proteínas/genes com Entrez Gene ID (NCBI).';
COMMENT ON COLUMN protein.gene_id    IS 'Entrez Gene ID (inteiro, chave natural do CSV).';
COMMENT ON COLUMN protein.name       IS 'Nome do gene/proteína (preenchido via enriquecimento).';


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. SIDE_EFFECT — Efeitos colaterais com código UMLS (CUI)
-- ─────────────────────────────────────────────────────────────────────────────
-- Cada efeito colateral é identificado por um código CUI do UMLS
-- (ex: C0151714 = hypermagnesemia). A categoria (Disease Class) vem do
-- arquivo bio-decagon-effectcategories.csv e classifica os 964 efeitos
-- em grandes grupos (ex: gastrointestinal system disease).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE side_effect (
    se_id       SERIAL       PRIMARY KEY,
    umls_cui    VARCHAR(20)  NOT NULL UNIQUE,
    name        VARCHAR(500) NOT NULL,
    category    VARCHAR(255)
);

COMMENT ON TABLE  side_effect            IS 'Efeitos colaterais com código UMLS CUI.';
COMMENT ON COLUMN side_effect.umls_cui   IS 'Concept Unique Identifier do UMLS (ex: C0151714).';
COMMENT ON COLUMN side_effect.name       IS 'Nome descritivo do efeito colateral.';
COMMENT ON COLUMN side_effect.category   IS 'Classe de doença (Disease Class) do effectcategories.csv.';


-- ─────────────────────────────────────────────────────────────────────────────
-- 4. DRUG_PROTEIN_TARGET — Relação droga → proteína-alvo
-- ─────────────────────────────────────────────────────────────────────────────
-- Representa quais proteínas cada droga tem como alvo terapêutico.
-- Fonte: bio-decagon-targets.csv (18.596 relações)
-- O CSV original NÃO contém evidence_score, mas a coluna é mantida para
-- futuro enriquecimento com dados de confiança (ex: STITCH confidence scores).
-- PK composta (drug_id, protein_id) garante unicidade do par.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE drug_protein_target (
    drug_id         INTEGER NOT NULL REFERENCES drug(drug_id)       ON DELETE CASCADE,
    protein_id      INTEGER NOT NULL REFERENCES protein(protein_id) ON DELETE CASCADE,
    evidence_score  NUMERIC(5,3),
    PRIMARY KEY (drug_id, protein_id)
);

COMMENT ON TABLE  drug_protein_target                IS 'Relações droga → proteína-alvo (targets).';
COMMENT ON COLUMN drug_protein_target.evidence_score IS 'Score de confiança (futuro enriquecimento).';


-- ─────────────────────────────────────────────────────────────────────────────
-- 5. PROTEIN_INTERACTION — Interações proteína-proteína (PPI)
-- ─────────────────────────────────────────────────────────────────────────────
-- Rede de interações proteína-proteína (PPI network) do BioGRID/STRING.
-- Fonte: bio-decagon-ppi.csv (719.402 arestas, 19.085 nós)
--
-- DECISÃO DE MODELAGEM — Simetria:
--   A relação PPI é simétrica (A interage com B ⟺ B interage com A).
--   Para evitar duplicatas, aplicamos a restrição protein_a_id < protein_b_id.
--   Isso garante que cada par seja armazenado exatamente uma vez.
--   Consultas devem considerar ambas as direções (OR/UNION).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE protein_interaction (
    protein_a_id    INTEGER NOT NULL REFERENCES protein(protein_id) ON DELETE CASCADE,
    protein_b_id    INTEGER NOT NULL REFERENCES protein(protein_id) ON DELETE CASCADE,
    PRIMARY KEY (protein_a_id, protein_b_id),
    CONSTRAINT chk_ppi_order CHECK (protein_a_id < protein_b_id)
);

COMMENT ON TABLE  protein_interaction IS 'Rede PPI (simétrica, armazenada com a < b).';
COMMENT ON CONSTRAINT chk_ppi_order ON protein_interaction
    IS 'Garante unicidade do par simétrico: protein_a_id sempre menor que protein_b_id.';


-- ─────────────────────────────────────────────────────────────────────────────
-- 6. DRUG_MONO_EFFECT — Efeitos colaterais de drogas individuais
-- ─────────────────────────────────────────────────────────────────────────────
-- Efeitos colaterais conhecidos de uma droga usada sozinha.
-- Fonte: bio-decagon-mono.csv (~487k linhas, SIDER + OFFSIDES)
--
-- O CSV NÃO contém um campo `source` explícito. A coluna é mantida para
-- futura anotação (ex: SIDER vs OFFSIDES).
-- PK composta (drug_id, se_id) garante unicidade.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE drug_mono_effect (
    drug_id     INTEGER NOT NULL REFERENCES drug(drug_id)         ON DELETE CASCADE,
    se_id       INTEGER NOT NULL REFERENCES side_effect(se_id)    ON DELETE CASCADE,
    source      VARCHAR(50),
    PRIMARY KEY (drug_id, se_id)
);

COMMENT ON TABLE  drug_mono_effect        IS 'Efeitos colaterais de drogas individuais (SIDER/OFFSIDES).';
COMMENT ON COLUMN drug_mono_effect.source IS 'Origem do dado: SIDER, OFFSIDES ou NULL (não disponível no CSV).';


-- ─────────────────────────────────────────────────────────────────────────────
-- 7. DRUG_COMBINATION_EFFECT — Efeitos colaterais de pares de drogas
-- ─────────────────────────────────────────────────────────────────────────────
-- Efeitos colaterais que surgem APENAS quando duas drogas são usadas juntas
-- (polifarmácia). Este é o core do domínio do projeto.
-- Fonte: bio-decagon-combo.csv (~4.65M linhas, TWOSIDES)
--
-- DECISÃO DE MODELAGEM — Simetria:
--   Assim como em protein_interaction, o par (drug_a, drug_b) é simétrico.
--   Restrição drug_a_id < drug_b_id evita duplicatas (CID_X, CID_Y) = (CID_Y, CID_X).
--
-- O CSV NÃO contém `n_reports`. A coluna é mantida para futuro enriquecimento
-- com dados do TWOSIDES sobre número de relatos.
--
-- PK composta em (drug_a_id, drug_b_id, se_id) porque o mesmo par de drogas
-- pode causar múltiplos efeitos colaterais distintos.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE drug_combination_effect (
    drug_a_id   INTEGER NOT NULL REFERENCES drug(drug_id)       ON DELETE CASCADE,
    drug_b_id   INTEGER NOT NULL REFERENCES drug(drug_id)       ON DELETE CASCADE,
    se_id       INTEGER NOT NULL REFERENCES side_effect(se_id)  ON DELETE CASCADE,
    n_reports   INTEGER,
    PRIMARY KEY (drug_a_id, drug_b_id, se_id),
    CONSTRAINT chk_combo_order CHECK (drug_a_id < drug_b_id)
);

COMMENT ON TABLE  drug_combination_effect             IS 'Efeitos colaterais de pares de drogas — polifarmácia (TWOSIDES).';
COMMENT ON COLUMN drug_combination_effect.n_reports   IS 'Número de relatos (futuro enriquecimento, não presente no CSV).';
COMMENT ON CONSTRAINT chk_combo_order ON drug_combination_effect
    IS 'Garante unicidade do par simétrico: drug_a_id sempre menor que drug_b_id.';


COMMIT;
