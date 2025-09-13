"""Módulo de autenticação JWT local para o Portal KNN.

Este módulo implementa autenticação JWT local como alternativa ao JWKS externo.
Ideal para desenvolvimento e produção quando não há servidor JWKS disponível.
"""

from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel

from src.auth import JWTPayload, get_current_user, security
from src.config import JWT_SECRET_KEY

router = APIRouter(tags=["authentication"])


class LoginRequest(BaseModel):
    """Modelo para requisição de login."""

    username: str
    password: str
    role: str | None = "student"  # student, admin, employee, partner


class LoginResponse(BaseModel):
    """Modelo para resposta de login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 horas em segundos
    user_info: dict


class TokenValidationResponse(BaseModel):
    """Modelo para resposta de validação de token."""

    valid: bool
    payload: dict | None = None
    error: str | None = None


# Usuários de exemplo (em produção, usar banco de dados)
TEST_USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "tenant": "knn",
        "name": "Administrador KNN",
    },
    "student": {
        "password": "student123",
        "role": "student",
        "tenant": "knn",
        "name": "Aluno Teste",
    },
    "employee": {
        "password": "employee123",
        "role": "employee",
        "tenant": "knn",
        "name": "Funcionário Teste",
    },
    "partner": {
        "password": "partner123",
        "role": "partner",
        "tenant": "knn",
        "name": "Parceiro Teste",
    },
}


def create_jwt_token(user_data: dict, expires_hours: int = 24) -> str:
    """Cria um token JWT válido.

    Args:
        user_data: Dados do usuário
        expires_hours: Horas até expiração do token

    Returns:
        Token JWT assinado
    """
    now = datetime.utcnow()
    payload = {
        "sub": user_data["username"],
        "role": user_data["role"],
        "tenant": user_data["tenant"],
        "exp": now + timedelta(hours=expires_hours),
        "iat": now,
        "iss": "knn-portal-local",
        "aud": "knn-portal",
        "name": user_data.get("name", user_data["username"]),
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def verify_jwt_token(token: str) -> JWTPayload:
    """Verifica e decodifica um token JWT local.

    Args:
        token: Token JWT para verificar

    Returns:
        Payload decodificado

    Raises:
        HTTPException: Se o token for inválido
    """
    try:
        payload_dict = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_aud": False}
        )
        return JWTPayload(**payload_dict)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido") from None


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Endpoint de login que gera JWT local.

    Args:
        request: Dados de login

    Returns:
        Token JWT e informações do usuário

    Raises:
        HTTPException: Se as credenciais forem inválidas
    """
    # Primeiro, tentar validar credenciais nos usuários de teste
    user = TEST_USERS.get(request.username)
    if user and user["password"] == request.password:
        # Verificar se o role solicitado é válido
        if request.role and request.role != user["role"]:
            raise HTTPException(
                status_code=403,
                detail=f"Usuário não tem permissão para role '{request.role}'",
            )

        # Preparar dados do usuário de teste
        user_data = {
            "username": request.username,
            "role": user["role"],
            "tenant": user["tenant"],
            "name": user["name"],
        }

        # Gerar token
        token = create_jwt_token(user_data)

        return LoginResponse(
            access_token=token,
            user_info={
                "username": request.username,
                "role": user["role"],
                "tenant": user["tenant"],
                "name": user["name"],
            },
        )

    # Se não encontrou nos usuários de teste, tentar autenticar com Firebase
    try:
        # Tentar obter usuário do Firebase por email
        firebase_user = firebase_auth.get_user_by_email(request.username)

        # Verificar se o usuário tem custom claims com role
        custom_claims = firebase_user.custom_claims or {}
        user_role = custom_claims.get("role", "student")
        user_tenant = custom_claims.get("tenant", "knn-dev-tenant")

        # Verificar se o role solicitado é válido
        if request.role and request.role != user_role:
            raise HTTPException(
                status_code=403,
                detail=f"Usuário não tem permissão para role '{request.role}'",
            )

        # Preparar dados do usuário Firebase
        user_data = {
            "username": firebase_user.email,
            "role": user_role,
            "tenant": user_tenant,
            "name": firebase_user.display_name or firebase_user.email,
        }

        # Gerar token
        token = create_jwt_token(user_data)

        return LoginResponse(
            access_token=token,
            user_info={
                "username": firebase_user.email,
                "role": user_role,
                "tenant": user_tenant,
                "name": firebase_user.display_name or firebase_user.email,
            },
        )

    except firebase_auth.UserNotFoundError:
        # Usuário não encontrado no Firebase
        pass
    except Exception as e:
        print(f"Erro ao autenticar com Firebase: {e}")
        pass

    # Se chegou até aqui, credenciais inválidas
    raise HTTPException(status_code=401, detail="Credenciais inválidas")


@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Endpoint para validar um token JWT.

    Args:
        credentials: Credenciais HTTP Bearer

    Returns:
        Resultado da validação do token
    """
    try:
        payload = verify_jwt_token(credentials.credentials)
        return TokenValidationResponse(valid=True, payload=payload.dict())
    except HTTPException as e:
        return TokenValidationResponse(valid=False, error=e.detail)


@router.get("/me")
async def get_me(
    current_user: JWTPayload = Depends(get_current_user),
):
    """Endpoint para obter informações do usuário atual.

    Args:
        current_user: Usuário autenticado obtido via dependência

    Returns:
        Informações do usuário autenticado
    """
    return {
        "username": current_user.sub,
        "role": current_user.role,
        "tenant": current_user.tenant,
        "name": current_user.name or current_user.sub,
        "expires_at": current_user.exp,
    }


@router.post("/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Endpoint para renovar um token JWT.

    Args:
        credentials: Credenciais HTTP Bearer

    Returns:
        Novo token JWT
    """
    # Verificar token atual
    payload = verify_jwt_token(credentials.credentials)

    # Gerar novo token
    user_data = {
        "username": payload.sub,
        "role": payload.role,
        "tenant": payload.tenant,
        "name": getattr(payload, "name", payload.sub),
    }

    new_token = create_jwt_token(user_data)

    return LoginResponse(
        access_token=new_token,
        user_info={
            "username": payload.sub,
            "role": payload.role,
            "tenant": payload.tenant,
            "name": getattr(payload, "name", payload.sub),
        },
    )
