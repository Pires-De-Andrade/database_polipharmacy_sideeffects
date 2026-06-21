"""
Loader de queries Cypher — lê ficheiros .cypher de cypher/queries/ e executa-os.

Nenhuma query Cypher é escrita inline neste módulo. Todas vivem nos ficheiros
.cypher versionados no repositório. Parâmetros são passados ao driver Neo4j
(não interpolados na string).
"""
from pathlib import Path

from app.backend.connections.neo4j_db import get_neo4j_driver, neo4j_database

# Pasta de queries Cypher: app/backend/queries/ → ../../../cypher/queries/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CYPHER_DIR = PROJECT_ROOT / "cypher" / "queries"


def load_cypher(filename: str) -> str:
    """Lê o conteúdo de um ficheiro .cypher e retorna como string."""
    path = CYPHER_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Query Cypher não encontrada: {path}")
    return path.read_text(encoding="utf-8")


def run_cypher(filename: str, params: dict | None = None) -> list[dict]:
    """
    Lê um ficheiro .cypher, executa-o no Neo4j e retorna uma lista de dicts.

    Os parâmetros são passados nativamente ao driver (ex: $stitch_a).
    """
    query = load_cypher(filename)
    driver = get_neo4j_driver()
    db = neo4j_database()
    with driver.session(database=db) as session:
        result = session.run(query, **(params or {}))
        return [record.data() for record in result]
