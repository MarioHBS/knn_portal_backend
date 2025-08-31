"""
Módulo de autenticação e autorização para o Portal de Benefícios KNN.
Implementa verificação de JWT com JWKS e validação de roles.
"""

import asyncio
import json
import time
from typing import Dict, Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

# Importações Firebase
import firebase_admin
import firebase_admin.auth

from src.config import (
    ENVIRONMENT,
    FIRESTORE_PROJECT,
    JWKS_CACHE_TTL,
    JWKS_URL,
    JWT_ALGORITHM,
    TESTING_MODE,
)

# Segurança para autenticação via Bearer token
security = HTTPBearer(auto_error=not TESTING_MODE)

# Cache para JWKS
jwks_cache = {"keys": None, "last_updated": 0}

# Inicialização do Firebase
def initialize_firebase():
    """Inicializa Firebase Admin SDK se não estiver inicializado."""
    try:
        if not firebase_admin._apps:
            # Tentar carregar credenciais do arquivo padrão
            from firebase_admin import credentials
            import os
            from pathlib import Path
            
            # Procurar arquivo de credenciais
            possible_paths = [
                "data/firestore_import/default-service-account-key.json",
                "default-service-account-key.json",
                os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
            ]
            
            cred_path = None
            for path in possible_paths:
                if path and Path(path).exists():
                    cred_path = path
                    break
            
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': FIRESTORE_PROJECT
                })
                print(f"Firebase inicializado com credenciais: {cred_path}")
            else:
                # Tentar inicializar com credenciais padrão do ambiente
                firebase_admin.initialize_app()
                print("Firebase inicializado com credenciais padrão do ambiente")
                
    except Exception as e:
        print(f"Erro ao inicializar Firebase: {e}")
        # Não falhar se Firebase não puder ser inicializado
        pass

# Inicializar Firebase na importação do módulo
initialize_firebase()


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
    Em modo de desenvolvimento, tenta primeiro Firebase Auth, depois JWKS externo.
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

    # Se credentials for uma string, usar diretamente
    if isinstance(credentials, str):
        token = credentials
    else:
        token = credentials.credentials

    # Em modo de desenvolvimento, tentar Firebase Auth primeiro
    if ENVIRONMENT == "development":
        try:
            # Primeiro, tentar verificar como ID token
            try:
                decoded_token = firebase_admin.auth.verify_id_token(token)
                print(f"Token verificado como ID token: {decoded_token.get('uid')}")
            except Exception as id_token_error:
                print(f"Não é um ID token válido: {id_token_error}")
                
                # Se não for ID token, pode ser custom token - decodificar diretamente
                import jwt
                import json
                
                # Decodificar sem verificação (apenas para desenvolvimento)
                decoded_token = jwt.decode(token, options={"verify_signature": False})
                print(f"Custom token decodificado: {json.dumps(decoded_token, indent=2)}")
                
                # Verificar se tem as informações necessárias
                if 'uid' in decoded_token or 'sub' in decoded_token:
                    uid = decoded_token.get('uid') or decoded_token.get('sub')
                    
                    # Buscar custom claims do usuário
                    user_record = firebase_admin.auth.get_user(uid)
                    custom_claims = user_record.custom_claims or {}
                    
                    print(f"Custom claims do usuário {uid}: {custom_claims}")
                    
                    # Usar custom claims do usuário
                    decoded_token.update(custom_claims)
            
            # Converter para JWTPayload
            uid = decoded_token.get('uid') or decoded_token.get('sub', '')
            payload = JWTPayload(
                sub=uid,
                exp=decoded_token.get('exp', 9999999999),
                iat=decoded_token.get('iat', int(time.time())),
                role=decoded_token.get('role', 'user'),
                tenant=decoded_token.get('tenant', 'default-tenant'),
                iss=decoded_token.get('iss'),
                aud=decoded_token.get('aud')
            )
            
            print(f"Token verificado com Firebase: {payload.sub} (role: {payload.role})")
            return payload
            
        except Exception as firebase_error:
            # Se Firebase falhar, tentar JWKS externo
            print(f"Firebase Auth falhou: {firebase_error}. Tentando JWKS externo...")
            import traceback
            print(f"Stack trace: {traceback.format_exc()}")
            pass

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
