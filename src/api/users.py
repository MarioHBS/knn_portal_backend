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
from src.config import JWT_SECRET_KEY, TESTING_MODE

router = APIRouter(tags=["authentication"])


class LoginRequest(BaseModel):
    """Modelo para requisição de login com credenciais."""

    username: str
    password: str
    role: str | None = "student"  # student, admin, employee, partner


class FirebaseLoginRequest(BaseModel):
    """Modelo para requisição de login com token Firebase."""

    firebase_token: str
    role: str | None = None  # Opcional, será extraído do token se não fornecido


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


def create_jwt_token(user_data: dict, expires_minutes: int = 30) -> str:
    """Cria um token JWT válido (HS256) padronizando o identificador (sub).

    Regras:
    - Usa 'sub' diretamente se fornecido.
    - Caso contrário, tenta 'username' e por fim 'email' para compatibilidade legada.
    - Não inclui 'name' no payload; esse dado pode ser obtido em endpoints específicos.

    Args:
        user_data: Dados do usuário
        expires_minutes: Minutos até expiração do token

    Returns:
        Token JWT assinado
    """
    now = datetime.utcnow()
    sub_value = user_data.get("sub") or user_data.get("username") or user_data.get("email")

    payload = {
        "sub": sub_value,
        "role": user_data["role"],
        "tenant": user_data["tenant"],
        "exp": now + timedelta(minutes=expires_minutes),
        "iat": now,
        "iss": "knn-portal-local",
        "aud": "knn-portal",
        # 'name' intencionalmente omitido; será consultado em endpoints próprios
        "entity_id": user_data.get("entity_id"),
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


@router.post("/login-legacy", response_model=LoginResponse)
async def login_legacy(request: LoginRequest):
    """Endpoint de login que gera JWT local (método legado).

    Args:
        request: Dados de login

    Returns:
        Token JWT e informações do usuário

    Raises:
        HTTPException: Se as credenciais forem inválidas
    """
    # Primeiro, tentar validar credenciais nos usuários de teste (apenas se TESTING_MODE estiver ativo)
    if TESTING_MODE:
        user = TEST_USERS.get(request.username)
        if (
            user
            and user["password"] == request.password
            and (not request.role or request.role == user["role"])
        ):
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
                expires_in=1800,  # 30 minutos em segundos
                user_info={
                    "username": request.username,
                    "role": user["role"],
                    "tenant": user["tenant"],
                    "name": user["name"],
                },
            )
        elif (
            user
            and user["password"] == request.password
            and request.role
            and request.role != user["role"]
        ):
            raise HTTPException(
                status_code=403,
                detail=f"Usuário não tem permissão para role '{request.role}'",
            )

    # Se não encontrou nos usuários de teste ou TESTING_MODE está desabilitado, tentar autenticar com Firebase
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
            expires_in=1800,  # 30 minutos em segundos
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


@router.post("/login", response_model=LoginResponse)
async def login(request: FirebaseLoginRequest):
    """Endpoint principal de login com token Firebase.

    Valida o token Firebase recebido e gera um JWT local com expiração de 30 minutos.
    Este é o método de autenticação recomendado.

    Args:
        request: Dados contendo o token Firebase

    Returns:
        Token JWT local e informações do usuário

    Raises:
        HTTPException: Se o token Firebase for inválido
    """
    # Se estiver em modo de teste, usar dados mock
    if TESTING_MODE:
        # Simular validação bem-sucedida para qualquer token em modo de teste
        user_data = {
            "username": "admin@knn.com.br",
            "role": "admin",
            "tenant": "test-tenant",
            "name": "Administrador Teste",
        }

        # Gerar token JWT local
        token = create_jwt_token(user_data)

        return LoginResponse(
            access_token=token,
            expires_in=1800,  # 30 minutos em segundos
            user_info={
                "username": "admin@knn.com.br",
                "role": "admin",
                "tenant": "test-tenant",
                "name": "Administrador Teste",
            },
        )

    try:
        # Importar a função de verificação do Firebase
        from src.auth import extract_data_from_firebase_token

        # Validar o token Firebase
        firebase_payload = await extract_data_from_firebase_token(
            request.firebase_token
        )

        # Extrair informações do usuário do token Firebase
        try:
            firebase_user = firebase_auth.get_user(firebase_payload.sub)
            user_email = firebase_user.email
            user_name = firebase_user.display_name or firebase_user.email
        except Exception:
            # Fallback se não conseguir obter dados do usuário
            user_email = firebase_payload.sub
            user_name = firebase_payload.name or firebase_payload.sub

        # Verificar role solicitado vs role do token
        token_role = firebase_payload.role
        if request.role and request.role != token_role:
            raise HTTPException(
                status_code=403,
                detail=f"Usuário não tem permissão para role '{request.role}'",
            )

        # Buscar entity_id na coleção users do Firestore usando o Firebase UID
        entity_id = None
        try:
            from src.db.firestore import get_database

            db = get_database()
            user_doc = db.collection("users").document(firebase_payload.sub).get()
            if user_doc.exists:
                user_data_firestore = user_doc.to_dict()
                entity_id = user_data_firestore.get("entity_id")
                print(f"DEBUG - Entity ID encontrado no Firestore: {entity_id}")
            else:
                print(
                    f"DEBUG - Documento do usuário não encontrado no Firestore para UID: {firebase_payload.sub}"
                )
        except Exception as e:
            # Log do erro mas não falhar o login se não conseguir buscar entity_id
            print(f"Aviso: Não foi possível buscar entity_id do Firestore: {e}")

        # Preparar dados do usuário (usar UID do Firebase como 'sub')
        user_data = {
            "sub": firebase_payload.sub,
            "role": token_role,
            "tenant": firebase_payload.tenant,
            "entity_id": entity_id,  # Incluir entity_id obtido do Firestore
        }

        # Gerar token JWT local com expiração de 30 minutos
        token = create_jwt_token(user_data, expires_minutes=30)

        return LoginResponse(
            access_token=token,
            expires_in=1800,  # 30 minutos em segundos
            user_info={
                "email": user_email,
                "role": token_role,
                "tenant": firebase_payload.tenant,
                "name": user_name,
            },
        )

    except HTTPException:
        # Re-raise HTTPExceptions (como token inválido)
        raise
    except Exception as e:
        # Capturar outros erros
        raise HTTPException(
            status_code=401,
            detail=f"Erro ao processar token Firebase: {str(e)}",
        ) from e


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
    # Buscar informações complementares do usuário no Firestore (first_access, entity_id)
    first_access = True
    entity_id = current_user.entity_id
    try:
        from src.db.firestore import get_database

        db = get_database()
        user_doc = db.collection("users").document(current_user.sub).get()
        if user_doc.exists:
            user_data_firestore = user_doc.to_dict()
            first_access = bool(user_data_firestore.get("first_access", True))
            # Preferir entity_id do Firestore se disponível
            entity_id = user_data_firestore.get("entity_id", entity_id)
    except Exception as e:
        # Não falhar se não conseguir buscar dados complementares
        print(f"Aviso: Não foi possível buscar dados do usuário no Firestore: {e}")

    return {
        "uid": current_user.sub,
        "role": current_user.role,
        "tenant": current_user.tenant,
        "expires_at": current_user.exp,
        "expires_at_iso": current_user.expires_iso(),
        "first_access": first_access,
        "entity_id": entity_id,
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
        "sub": payload.sub,
        "role": payload.role,
        "tenant": payload.tenant,
    }

    new_token = create_jwt_token(user_data, expires_minutes=30)

    return LoginResponse(
        access_token=new_token,
        expires_in=1800,  # 30 minutos em segundos
        user_info={
            "username": payload.sub,
            "role": payload.role,
            "tenant": payload.tenant,
            "name": getattr(payload, "name", payload.sub),
        },
    )


class FirebaseTokenRequest(BaseModel):
    """Modelo para requisição de teste de token Firebase."""

    token: str


class FirebaseTokenResponse(BaseModel):
    """Modelo para resposta de teste de token Firebase."""

    message: str
    token_valid: bool
    user_info: dict | None = None


@router.post("/test-firebase-token")
async def test_firebase_token(request: FirebaseTokenRequest):
    """Endpoint de teste exclusivo para receber e validar tokens Firebase.

    Este endpoint é usado para testar a recepção e validação de tokens Firebase
    enviados pelo frontend. Retorna uma confirmação de recebimento e o status
    de validação do token.

    Args:
        request: Objeto contendo o token Firebase

    Returns:
        Mensagem de confirmação e informações de validação
    """
    try:
        # Importar a função de verificação do Firebase
        from src.auth import extract_data_from_firebase_token

        # Tentar validar o token Firebase
        payload = await extract_data_from_firebase_token(request.token)

        return FirebaseTokenResponse(
            message="OK, token recebido e validado com sucesso",
            token_valid=True,
            user_info={
                "sub": payload.sub,
                "email": getattr(payload, "email", None),
                "role": payload.role,
                "tenant": payload.tenant,
                "exp": payload.exp,
            },
        )

    except HTTPException as e:
        # Token inválido ou erro de validação
        return FirebaseTokenResponse(
            message=f"OK, token recebido mas inválido: {e.detail}",
            token_valid=False,
        )

    except Exception as e:
        # Erro inesperado
        return FirebaseTokenResponse(
            message=f"OK, token recebido mas erro na validação: {str(e)}",
            token_valid=False,
        )
