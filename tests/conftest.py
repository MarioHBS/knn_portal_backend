"""
Configurações globais para testes pytest.
"""

# IMPORTANTE: Definir variáveis de ambiente ANTES de qualquer importação
import os

os.environ["TESTING_MODE"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["KNN_USE_TEST_DATABASE"] = "true"
os.environ["FIRESTORE_PROJECT"] = "test-project"

from unittest.mock import patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Configura o ambiente de teste automaticamente para todos os testes.
    """
    # Ativar modo de teste
    os.environ["TESTING_MODE"] = "true"

    # Configurar outras variáveis de ambiente necessárias para testes
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "true"
    os.environ["KNN_USE_TEST_DATABASE"] = "true"

    # Configurar variáveis do Firebase para teste (evitar conexões reais)
    os.environ["FIRESTORE_PROJECT"] = "test-project"

    yield

    # Cleanup após os testes (opcional)
    # Remover variáveis de ambiente se necessário
    pass


@pytest.fixture(autouse=True)
def mock_firestore_for_all_tests():
    """
    Mock do Firestore para todos os testes automaticamente.
    """
    with patch("src.api.admin.firestore_client") as mock_firestore:
        # Configurar comportamento padrão do mock
        mock_firestore.collection.return_value.stream.return_value = []
        mock_firestore.collection.return_value.document.return_value.get.return_value.exists = False
        yield mock_firestore
