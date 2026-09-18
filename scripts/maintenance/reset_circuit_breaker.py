#!/usr/bin/env python3
"""
Script temporário para resetar o circuit breaker e testar o Firestore.
"""

import os
import sys

# Adicionar o diretório raiz do projeto ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.db.circuit_breaker import circuit_breaker
from src.utils import logger


def main():
    """Reseta o circuit breaker e mostra o status."""
    logger.info(f"Estado atual do circuit breaker: {circuit_breaker.state}")
    logger.info(f"Falhas consecutivas: {circuit_breaker.failures}")

    # Resetar o circuit breaker
    circuit_breaker.reset()

    logger.info(f"Novo estado do circuit breaker: {circuit_breaker.state}")
    logger.info(f"Falhas consecutivas: {circuit_breaker.failures}")

    print("✅ Circuit breaker resetado com sucesso!")


if __name__ == "__main__":
    main()
