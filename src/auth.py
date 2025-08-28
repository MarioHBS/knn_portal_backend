"""
Módulo de autenticação e autorização para o Portal de Benefícios KNN.
Implementa verificação de JWT com JWKS e validação de roles.
"""

import time

import httpx
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from src.config import JWKS_CACHE_TTL, JWKS_URL, JWT_ALGORITHM, TESTING_MODE

# Segurança para autenticação via Bearer token
security = HTTPBearer(auto_error=not TESTING_MODE)

# Cache para JWKS
jwks_cache = {"keys": None, "last_updated": 0}


class JWTPayload(BaseModel):
    """Modelo para o payload do JWT."""

    sub: str
    role: str
    tenant: str
    exp: int
    iat: int
    iss: str | None = None
    aud: str | list[str] | None = None


async def get_jwks() -> dict:
    """
    Obtém as chaves JWKS do servidor de autenticação com cache.
    """
    global jwks_cache
    current_time = time.time()

    # Verificar se o cache está válido
    if (
        jwks_cache["keys"] is None
        or current_time - jwks_cache["last_updated"] > JWKS_CACHE_TTL
    ):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(JWKS_URL)
                response.raise_for_status()
                jwks_cache["keys"] = response.json()
                jwks_cache["last_updated"] = current_time
        except Exception:
            # Se falhar e não tivermos cache, levanta exceção
            if jwks_cache["keys"] is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": {"code": "JWKS_ERROR", "msg": "Erro ao obter JWKS"}
                    },
                ) from None
            # Se falhar mas temos cache, usa o cache existente

    return jwks_cache["keys"]


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> JWTPayload:
    """
    Verifica o token JWT e retorna o payload.
    """
    # Se estiver em modo de teste, retornar dados mock
    if TESTING_MODE:
        return JWTPayload(
            sub="test-user-123",
            role="user",
            tenant="test-tenant",
            exp=9999999999,
            iat=1000000000,
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "msg": "Token não fornecido"}},
        )

    token = credentials.credentials

    try:
        # Obter JWKS
        jwks = await get_jwks()

        # Decodificar cabeçalho para obter kid
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "INVALID_TOKEN", "msg": "Token sem kid"}},
            )

        # Encontrar chave correspondente
        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {"code": "INVALID_TOKEN", "msg": "Chave não encontrada"}
                },
            )

        # Verificar token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False},  # Configurar conforme necessidade
        )

        return JWTPayload(**payload)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "msg": "Token inválido"}},
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "msg": str(e)}},
        ) from e


async def get_current_user(token: JWTPayload = Depends(verify_token)) -> JWTPayload:
    """
    Obtém o usuário atual a partir do token JWT.
    """
    # Se estiver em modo de teste, retornar dados mock
    if TESTING_MODE:
        return JWTPayload(
            sub="test-user-123",
            role="user",
            tenant="test-tenant",
            exp=9999999999,
            iat=1000000000,
        )
    return token


async def validate_student_role(
    token: JWTPayload = Depends(get_current_user),
) -> JWTPayload:
    """
    Valida se o usuário tem role de aluno.
    """
    # Se estiver em modo de teste, retornar dados mock
    if TESTING_MODE:
        return JWTPayload(
            sub="test-student-123",
            role="student",
            tenant="test-tenant",
            exp=9999999999,
            iat=1000000000,
        )

    if token.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "msg": "Acesso permitido apenas para alunos",
                }
            },
        )
    return token


async def validate_partner_role(
    token: JWTPayload = Depends(get_current_user),
) -> JWTPayload:
    """
    Valida se o usuário tem role de parceiro.
    """
    # Se estiver em modo de teste, retornar dados mock
    if TESTING_MODE:
        return JWTPayload(
            sub="test-partner-123",
            role="partner",
            tenant="test-tenant",
            exp=9999999999,
            iat=1000000000,
        )

    if token.role != "partner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "msg": "Acesso permitido apenas para parceiros",
                }
            },
        )
    return token


async def validate_admin_role(
    token: JWTPayload = Depends(get_current_user),
) -> JWTPayload:
    """
    Valida se o usuário tem role de administrador.
    """
    # Se estiver em modo de teste, retornar dados mock
    if TESTING_MODE:
        return JWTPayload(
            sub="test-admin-123",
            role="admin",
            tenant="test-tenant",
            exp=9999999999,
            iat=1000000000,
        )

    if token.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "msg": "Acesso permitido apenas para administradores",
                }
            },
        )
    return token


async def validate_employee_role(
    token: JWTPayload = Depends(get_current_user),
) -> JWTPayload:
    """
    Valida se o usuário tem role de funcionário.
    """
    # Se estiver em modo de teste, retornar dados mock
    if TESTING_MODE:
        return JWTPayload(
            sub="test-employee-123",
            role="employee",
            tenant="test-tenant",
            exp=9999999999,
            iat=1000000000,
        )

    if token.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "msg": "Acesso permitido apenas para funcionários",
                }
            },
        )
    return token
