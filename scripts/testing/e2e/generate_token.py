"""
Script para gerar token JWT local para testes.
"""
import argparse
from datetime import UTC, datetime, timedelta

import jwt

# Configurações do token
SECRET_KEY = "knn-dev-jwt-secret-2025-change-in-production"
ALGORITHM = "HS256"


def generate_token(role: str = "admin", user_id: str = "admin-test-123", entity_id: str | None = None):
    """Gera um token JWT local válido."""
    # Usar timezone UTC para evitar problemas de fuso horário
    now = datetime.now(UTC)

    payload = {
        "sub": user_id,
        "role": role,
        "tenant": "knn-dev-tenant",
        "iat": int(now.timestamp()),  # Issued at - agora
        "exp": int((now + timedelta(hours=24)).timestamp()),  # Expires - 24 horas
    }

    if entity_id:
        payload["entity_id"] = entity_id

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    print("✅ Token gerado com sucesso!")
    print(f"👤 Role: {role}")
    print(f"🆔 User ID: {user_id}")
    if entity_id:
        print(f"🏢 Entity ID: {entity_id}")
    print(f"🕐 Issued at: {now}")
    print(f"⏰ Expires at: {now + timedelta(hours=24)}")
    print(f"🏢 Tenant: {payload['tenant']}")
    print(f"🔑 Token: {token}")

    # Salvar token em arquivo
    with open("scripts/testing/e2e/access_token.txt", "w") as f:
        f.write(token)

    print("💾 Token salvo em scripts/testing/e2e/access_token.txt")

    return token


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerar token JWT de teste.")
    parser.add_argument("--role", type=str, default="admin", help="Perfil do usuário (ex: admin, student)")
    parser.add_argument("--user_id", type=str, default="admin-test-123", help="ID do usuário")
    parser.add_argument("--entity_id", type=str, default=None, help="ID da entidade a ser incluído no token")
    args = parser.parse_args()

    generate_token(role=args.role, user_id=args.user_id, entity_id=args.entity_id)
