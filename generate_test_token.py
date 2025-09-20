#!/usr/bin/env python3
"""
Script para gerar token JWT de teste com o tenant correto.
"""

from datetime import datetime, timedelta

import jwt

# Payload do token
payload = {
    "sub": "aluno.teste@journeyclub.com.br",
    "role": "student",
    "tenant": "knn-dev-tenant",  # Tenant correto
    "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),
    "iat": int(datetime.utcnow().timestamp()),
    "iss": "knn-portal-local",
    "aud": "knn-portal",
    "name": "João Silva Santos",
}

# Chave secreta (mesma usada no servidor)
secret_key = "knn-dev-jwt-secret-key-change-in-production"

# Gerar token
token = jwt.encode(payload, secret_key, algorithm="HS256")

print("Token JWT gerado:")
print(token)
print("\nPayload:")
print(payload)
