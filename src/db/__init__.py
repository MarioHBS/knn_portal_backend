"""
Inicialização do pacote de banco de dados.

Este módulo configura e exporta os clientes de banco de dados necessários
para a aplicação, incluindo Firestore, PostgreSQL, Storage e Circuit Breaker.
"""

import os

# Determina se estamos em modo de teste
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

if TEST_MODE:
    # Importa clientes simulados para testes
    from .mock_db import (
        mock_circuit_breaker as circuit_breaker,
    )
    from .mock_db import (
        mock_firestore as firestore_client,
    )
    from .mock_db import (
        mock_postgres as postgres_client,
    )
    from .mock_db import (
        mock_storage_client as storage_client,
    )
    from .mock_db import (
        with_mock_circuit_breaker as with_circuit_breaker,
    )
else:
    # Importa clientes reais para produção
    from .circuit_breaker import circuit_breaker, with_circuit_breaker
    from .firestore import firestore_client
    from .postgres import postgres_client
    from .storage import storage_client

__all__ = [
    "firestore_client",
    "postgres_client",
    "storage_client",
    "circuit_breaker",
    "with_circuit_breaker",
]
