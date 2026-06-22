"""
Resolução de nomes de medicamentos na camada da aplicação.

Os CSVs do DECAGON só trazem o STITCH ID (ex: CID000002173). O mapa
`app/data/drug_names.json` — gerado offline via PubChem por
`etl/build_drug_names.py` — traduz esses IDs para nomes legíveis.

A resolução acontece aqui, em memória, em vez de na coluna `drug.name` do
banco. Vantagens: não exige migração/enriquecimento por instância e funciona
igual para o banco local e o oficial na nuvem.
"""
import json
from functools import lru_cache
from pathlib import Path

# Raiz do projecto: app/backend/ → ../../
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DRUG_NAMES_FILE = PROJECT_ROOT / "app" / "data" / "drug_names.json"


@lru_cache(maxsize=1)
def load_drug_names() -> dict[str, str]:
    """Mapa STITCH ID → nome legível (cacheado, lido uma vez por processo)."""
    if DRUG_NAMES_FILE.exists():
        return json.loads(DRUG_NAMES_FILE.read_text(encoding="utf-8"))
    return {}


def resolve_name(stitch_id: str | None, fallback: str | None = None) -> str:
    """Nome legível do medicamento; cai no stitch_id quando não resolvido."""
    if not stitch_id:
        return fallback or ""
    return load_drug_names().get(stitch_id, fallback or stitch_id)
