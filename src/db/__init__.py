"""
Inicialização do pacote de banco de dados.
"""
import os

# Verificar se estamos em ambiente de teste
TEST_MODE = os.environ.get("KNN_USE_TEST_DATABASE", "false").lower() == "true"

if TEST_MODE:
    # Usar implementações simuladas para testes
    from src.db.mock_db import mock_circuit_breaker as circuit_breaker
    from src.db.mock_db import mock_firestore as firestore_client
    from src.db.mock_db import mock_postgres as postgres_client
    from src.db.mock_db import with_mock_circuit_breaker as with_circuit_breaker

    print("Usando banco de dados simulado para testes")
else:
    # Usar implementações reais para produção
    from src.db.circuit_breaker import circuit_breaker, with_circuit_breaker
    from src.db.firestore import firestore_client
    from src.db.postgres import postgres_client

__all__ = [
    "firestore_client",
    "postgres_client",
    "circuit_breaker",
    "with_circuit_breaker",
]
