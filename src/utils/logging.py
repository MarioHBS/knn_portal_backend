"""
Utilitários para logging estruturado com mascaramento de CPF.
"""

import re
from typing import Any

import structlog

# Padrão para identificar CPFs em strings
CPF_PATTERN = re.compile(r"\b\d{11}\b")
CPF_MASKED = "***********"


def mask_cpf(text: str) -> str:
    """
    Mascara CPFs em uma string.
    """
    return CPF_PATTERN.sub(CPF_MASKED, text)


def mask_cpf_in_log(log_event: dict[str, Any] | str) -> dict[str, Any] | str:
    """
    Mascara CPFs em eventos de log, seja dicionário ou string.
    """
    if isinstance(log_event, dict):
        masked_event = {}
        for key, value in log_event.items():
            if key.lower() == "cpf" or "cpf" in key.lower():
                masked_event[key] = CPF_MASKED
            elif isinstance(value, str):
                masked_event[key] = mask_cpf(value)
            elif isinstance(value, dict):
                masked_event[key] = mask_cpf_in_log(value)
            else:
                masked_event[key] = value
        return masked_event
    elif isinstance(log_event, str):
        return mask_cpf(log_event)
    return log_event


# Configuração do structlog
def configure_logging():
    """
    Configura o logging estruturado com mascaramento de CPF.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            # Processor personalizado para mascarar CPFs
            lambda logger, method_name, event_dict: {
                "event": mask_cpf_in_log(event_dict.get("event", "")),
                **mask_cpf_in_log(
                    {k: v for k, v in event_dict.items() if k != "event"}
                ),
            },
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
        cache_logger_on_first_use=True,
    )


# Obter logger configurado
logger = structlog.get_logger()
