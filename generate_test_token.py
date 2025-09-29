#!/usr/bin/env python3
"""
Script para gerar token JWT de teste com o tenant correto.
"""

from datetime import datetime, timedelta, timezone

import jwt

# Payload do token
payload = {
    "sub": "admin@knn.com.br",
    "role": "admin",
    "tenant": "knn-dev-tenant",  # Tenant correto
    "exp": int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()),
    "iat": int(datetime.now(timezone.utc).timestamp()),
    "iss": "knn-portal-local",
    "aud": "knn-portal",
    "name": "Admin KNN",
}

# Chave secreta (mesma usada no servidor)
secret_key = "knn-dev-jwt-secret-2025-change-in-production"

# Gerar token
token = jwt.encode(payload, secret_key, algorithm="HS256")

print("Token JWT gerado:")
print(token)
print("\nPayload:")
print(payload)
