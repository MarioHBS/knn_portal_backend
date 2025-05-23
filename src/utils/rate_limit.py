"""
Utilitários para rate limiting.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Configuração do rate limiter baseado no endereço IP
limiter = Limiter(key_func=get_remote_address)
