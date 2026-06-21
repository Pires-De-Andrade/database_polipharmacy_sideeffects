"""
Context manager para medir tempo de execução de queries.

Uso:
    with QueryTimer() as t:
        result = run_some_query()
    print(f"Executado em {t.elapsed_ms:.1f}ms")
"""
import time


class QueryTimer:
    """Mede o tempo decorrido dentro de um bloco `with`, em milissegundos."""

    def __init__(self):
        self.elapsed_ms: float = 0.0
        self._start: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000.0
        return False  # não suprime excepções
