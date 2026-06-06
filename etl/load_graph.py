#!/usr/bin/env python3
"""
==============================================================================
Projeto BD Polifarmácia — ETL: Carga dos CSVs no Neo4j
==============================================================================
Carrega os datasets do DECAGON no banco de grafos Neo4j.

Uso:
    python load_graph.py                    # carga completa
    python load_graph.py --sample 1000     # apenas primeiras 1000 linhas/CSV

Variáveis de ambiente (.env):
    NEO4J_URI      (default: bolt://localhost:7687)
    NEO4J_USER     (default: neo4j)
    NEO4J_PASSWORD (default: neo4j)

TODO: Implementar nas próximas etapas do projeto.
==============================================================================
"""

# Implementação será adicionada na próxima etapa.
# Estrutura planejada:
#   1. Criar constraints (constraints.cypher)
#   2. Carregar nós :Drug, :Protein, :SideEffect
#   3. Carregar arestas :TARGETS, :INTERACTS_WITH, :CAUSES_COMBINED, :HAS_MONO_EFFECT
#   4. Suporte a --sample para testes rápidos

print("⚠ load_graph.py ainda não implementado. Próxima etapa.")
