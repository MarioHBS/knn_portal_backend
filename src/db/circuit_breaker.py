"""
Implementação do circuit breaker para fallback entre Firestore e PostgreSQL.
"""
import time
from typing import Dict, List, Optional, Any, Union, Callable
from functools import wraps

from src.config import CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_TIMEOUT
from src.utils import logger

class CircuitBreaker:
    """
    Implementação de circuit breaker para fallback entre Firestore e PostgreSQL.
    """
    def __init__(self):
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    def record_failure(self):
        """
        Registra uma falha no Firestore.
        """
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= CIRCUIT_BREAKER_THRESHOLD:
            self.state = "open"
            logger.warning(f"Circuit breaker aberto após {self.failures} falhas consecutivas")
    
    def record_success(self):
        """
        Registra um sucesso no Firestore.
        """
        self.failures = 0
        self.state = "closed"
    
    def can_execute(self):
        """
        Verifica se o Firestore pode ser acessado.
        """
        if self.state == "closed":
            return True
        
        if self.state == "open":
            # Verificar se já passou o tempo de timeout
            if time.time() - self.last_failure_time > CIRCUIT_BREAKER_TIMEOUT:
                self.state = "half-open"
                logger.info("Circuit breaker em estado half-open, tentando Firestore novamente")
                return True
            return False
        
        # Estado half-open
        return True

# Instância global do circuit breaker
circuit_breaker = CircuitBreaker()

async def with_circuit_breaker(
    firestore_func: Callable, 
    postgres_func: Callable, 
    *args, **kwargs
) -> Any:
    """
    Executa uma função com circuit breaker, fazendo fallback para PostgreSQL se necessário.
    
    Args:
        firestore_func: Função do Firestore a ser executada
        postgres_func: Função do PostgreSQL a ser executada como fallback
        *args, **kwargs: Argumentos para as funções
    
    Returns:
        Resultado da função
    """
    if circuit_breaker.can_execute():
        try:
            # Tentar Firestore
            result = await firestore_func(*args, **kwargs)
            circuit_breaker.record_success()
            return result
        except Exception as e:
            # Registrar falha
            circuit_breaker.record_failure()
            logger.error(f"Erro no Firestore, fazendo fallback para PostgreSQL: {str(e)}")
    else:
        logger.info("Circuit breaker aberto, usando PostgreSQL diretamente")
    
    # Fallback para PostgreSQL
    try:
        return await postgres_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Erro no fallback para PostgreSQL: {str(e)}")
        raise
