"""Sistema robusto de tratamento de erros para operações de banco de dados.

Este módulo fornece classes e decoradores para tratamento de erros,
retry automático, logging e validações.
"""

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any

from src.utils import logger


class DatabaseError(Exception):
    """Exceção base para erros de banco de dados."""

    def __init__(self, message: str, error_code: str = None, original_error=None):
        super().__init__(message)
        self.error_code = error_code
        self.original_error = original_error
        self.timestamp = time.time()


class ConnectionError(DatabaseError):
    """Erro de conexão com banco de dados."""

    pass


class ValidationError(DatabaseError):
    """Erro de validação de dados."""

    pass


class TimeoutError(DatabaseError):
    """Erro de timeout em operações."""

    pass


class AuthenticationError(DatabaseError):
    """Erro de autenticação."""

    pass


class PermissionError(DatabaseError):
    """Erro de permissão/autorização."""

    pass


class RetryConfig:
    """Configuração para retry automático."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


# Configuração padrão de retry
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3, base_delay=1.0, max_delay=60.0, exponential_base=2.0, jitter=True
)


class ErrorHandler:
    """Classe principal para tratamento de erros."""

    @staticmethod
    def classify_error(error: Exception) -> DatabaseError:
        """Classifica um erro em uma exceção específica.

        Args:
            error: Exceção original

        Returns:
            Exceção classificada
        """
        error_message = str(error)
        error_lower = error_message.lower()

        # Erros de conexão
        if any(
            keyword in error_lower
            for keyword in [
                "connection",
                "network",
                "timeout",
                "unreachable",
                "refused",
            ]
        ):
            return ConnectionError(
                f"Erro de conexão: {error_message}",
                error_code="CONNECTION_FAILED",
                original_error=error,
            )

        # Erros de autenticação
        if any(
            keyword in error_lower
            for keyword in ["auth", "credential", "permission", "unauthorized"]
        ):
            return AuthenticationError(
                f"Erro de autenticação: {error_message}",
                error_code="AUTH_FAILED",
                original_error=error,
            )

        # Erros de validação
        if any(
            keyword in error_lower
            for keyword in ["validation", "invalid", "required", "format"]
        ):
            return ValidationError(
                f"Erro de validação: {error_message}",
                error_code="VALIDATION_FAILED",
                original_error=error,
            )

        # Erros de timeout
        if "timeout" in error_lower:
            return TimeoutError(
                f"Timeout: {error_message}",
                error_code="TIMEOUT",
                original_error=error,
            )

        # Erro genérico de banco
        return DatabaseError(
            f"Erro de banco de dados: {error_message}",
            error_code="DATABASE_ERROR",
            original_error=error,
        )

    @staticmethod
    async def retry_with_backoff(
        func: Callable, config: RetryConfig, *args, **kwargs
    ) -> Any:
        """Executa uma função com retry e backoff exponencial.

        Args:
            func: Função a ser executada
            config: Configuração de retry
            *args: Argumentos da função
            **kwargs: Argumentos nomeados da função

        Returns:
            Resultado da função

        Raises:
            DatabaseError: Se todas as tentativas falharem
        """
        last_error = None

        for attempt in range(config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                last_error = e
                classified_error = ErrorHandler.classify_error(e)

                # Se é a última tentativa, não esperar
                if attempt == config.max_attempts - 1:
                    logger.warning(
                        f"Tentativa {attempt + 1}/{config.max_attempts} falhou",
                        extra={
                            "error": str(e),
                            "error_type": type(classified_error).__name__,
                            "error_code": classified_error.error_code,
                            "function": func.__name__,
                            "attempt": attempt + 1,
                        },
                    )
                    break

                # Calcular delay com backoff exponencial
                delay = min(
                    config.base_delay * (config.exponential_base**attempt),
                    config.max_delay,
                )

                # Adicionar jitter se configurado
                if config.jitter:
                    import random

                    delay *= 0.5 + random.random() * 0.5

                logger.warning(
                    f"Tentativa {attempt + 1}/{config.max_attempts} falhou",
                    extra={
                        "error": str(e),
                        "error_type": type(classified_error).__name__,
                        "error_code": classified_error.error_code,
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "delay": delay,
                    },
                )

                logger.info(f"Aguardando {delay:.2f}s antes da próxima tentativa")
                await asyncio.sleep(delay)

        # Se chegou aqui, todas as tentativas falharam
        final_error = ErrorHandler.classify_error(last_error)
        logger.error(
            f"Todas as {config.max_attempts} tentativas falharam",
            extra={
                "error": str(last_error),
                "error_code": final_error.error_code,
                "function": func.__name__,
            },
        )
        raise final_error

    @staticmethod
    def log_error(error: Exception, context: dict[str, Any] = None) -> None:
        """Registra um erro com contexto detalhado.

        Args:
            error: Exceção a ser registrada
            context: Contexto adicional para o log
        """
        context = context or {}

        if isinstance(error, DatabaseError):
            logger.error(
                f"Erro de banco: {error}",
                extra={
                    "error_code": error.error_code,
                    "timestamp": error.timestamp,
                    "original_error": str(error.original_error)
                    if error.original_error
                    else None,
                    **context,
                },
            )
        else:
            logger.error(
                f"Erro não classificado: {error}",
                extra={"error_type": type(error).__name__, **context},
            )


def validate_required_fields(data: dict[str, Any], required_fields: list[str]) -> None:
    """Valida se todos os campos obrigatórios estão presentes.

    Args:
        data: Dados a serem validados
        required_fields: Lista de campos obrigatórios

    Raises:
        ValidationError: Se algum campo obrigatório estiver ausente
    """
    missing_fields = [
        field for field in required_fields if field not in data or data[field] is None
    ]

    if missing_fields:
        raise ValidationError(
            f"Campos obrigatórios ausentes: {', '.join(missing_fields)}",
            error_code="MISSING_REQUIRED_FIELDS",
        )


def validate_tenant_access(tenant_id: str, user_tenant: str) -> None:
    """Valida se o usuário tem acesso ao tenant.

    Args:
        tenant_id: ID do tenant solicitado
        user_tenant: ID do tenant do usuário

    Raises:
        PermissionError: Se o acesso for negado
    """
    if tenant_id != user_tenant:
        raise PermissionError(
            f"Acesso negado ao tenant '{tenant_id}'",
            error_code="TENANT_ACCESS_DENIED",
        )


async def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """Executa uma função de forma segura com tratamento de erros.

    Args:
        func: Função a ser executada
        *args: Argumentos da função
        **kwargs: Argumentos nomeados da função

    Returns:
        Resultado da função ou None se houver erro
    """
    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    except Exception as e:
        ErrorHandler.log_error(e, {"function": func.__name__})
        return None


def with_error_handling(retry_config: RetryConfig = None, operation_name: str = None):
    """Decorator para adicionar tratamento de erros e retry a funções.

    Args:
        retry_config: Configuração de retry (usa padrão se None)
        operation_name: Nome da operação para logs

    Returns:
        Decorator function
    """
    if retry_config is None:
        retry_config = DEFAULT_RETRY_CONFIG

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__

            try:
                logger.debug(f"Iniciando operação: {op_name}")
                start_time = time.time()

                result = await ErrorHandler.retry_with_backoff(
                    func, retry_config, *args, **kwargs
                )

                duration = time.time() - start_time
                logger.info(
                    f"Operação '{op_name}' concluída com sucesso",
                    extra={"duration": duration, "operation": op_name},
                )

                return result

            except Exception as e:
                ErrorHandler.log_error(
                    e, {"operation": op_name, "args": str(args), "kwargs": str(kwargs)}
                )
                raise

        return wrapper

    return decorator
