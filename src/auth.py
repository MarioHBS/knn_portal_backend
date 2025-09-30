"""
Módulo de autenticação e autorização para o Portal de Benefícios KNN.
Implementa verificação de JWT com JWKS e validação de roles.
"""

# Importações Firebase
import firebase_admin
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth
from pydantic import BaseModel

from src.config import (
    ENVIRONMENT,
    FIRESTORE_PROJECT,
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
        # Verificar se Firebase já foi inicializado
        if firebase_admin._apps:
            print("Firebase já inicializado, reutilizando conexão")
            return

        # Tentar carregar credenciais do arquivo padrão
        import os
        from pathlib import Path

        from firebase_admin import credentials

        # Procurar arquivo de credenciais
        possible_paths = [
            "credentials/default-service-account-key.json",
            "data/firestore_import/default-service-account-key.json",
            "default-service-account-key.json",
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        ]

        cred_path = None
        for path in possible_paths:
            if path and Path(path).exists():
                cred_path = path
                break

        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {"projectId": FIRESTORE_PROJECT})
            print(f"Firebase inicializado com credenciais: {cred_path}")
        else:
            # Tentar inicializar com credenciais padrão do ambiente
            try:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {"projectId": FIRESTORE_PROJECT})
                print("Firebase inicializado com credenciais padrão do ambiente")
            except Exception as e:
                print(f"Aviso: Não foi possível usar credenciais padrão: {e}")
                # Fallback para modo emulador/teste
                firebase_admin.initialize_app(options={"projectId": FIRESTORE_PROJECT})
                print("Firebase inicializado em modo emulador/teste")

    except Exception as e:
        print(f"Erro ao inicializar Firebase: {e}")
        # Não falhar se Firebase não puder ser inicializado
        pass


# Inicializar Firebase na importação do módulo
initialize_firebase()


class JWTPayload(BaseModel):
    """Modelo para o payload do JWT.

    Attributes:
        sub: Subject - Identificador único do usuário (user ID)
        role: Papel/função do usuário no sistema (admin, employee, student, partner)
        tenant: Identificador do tenant/organização do usuário
        exp: Expiration time - Timestamp Unix de quando o token expira
        iat: Issued at - Timestamp Unix de quando o token foi emitido
        iss: Issuer - Identificador do emissor do token (opcional)
        aud: Audience - Audiência pretendida do token, pode ser string ou lista (opcional)
        name: Nome do usuário (opcional)
        entity_id: ID da entidade associada ao usuário
    """

    sub: str
    role: str
    tenant: str
    exp: int
    iat: int
    iss: str | None = None
    aud: str | list[str] | None = None
    name: str | None = None
    entity_id: str | None = None


async def verify_firebase_token(token: str) -> JWTPayload:
    """
    Verifica o token de ID do Firebase e retorna o payload padronizado.
    """
    try:
        decoded_token = auth.verify_id_token(token)
        # Padroniza o payload para o modelo JWTPayload
        return JWTPayload(
            sub=decoded_token.get("uid", ""),
            role=decoded_token.get("role", "student"),
            tenant=decoded_token.get("tenant", "knn-dev-tenant"),
            exp=decoded_token.get("exp", 0),
            iat=decoded_token.get("iat", 0),
            iss=decoded_token.get("iss"),
            aud=decoded_token.get("aud"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_FIREBASE_TOKEN", "msg": str(e)}},
        ) from e


async def verify_local_jwt(token: str) -> JWTPayload:
    """
    Verifica um token JWT local (HS256) usado para desenvolvimento e testes.
    """
    import jwt

    from src.config import JWT_SECRET_KEY

    try:
        payload_dict = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return JWTPayload(**payload_dict)
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_LOCAL_JWT", "msg": str(e)}},
        ) from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> JWTPayload:
    """
    Dependência FastAPI para obter o usuário atual.

    - Em modo de teste, retorna um usuário mock.
    - Em produção, valida estritamente com o Firebase.
    - Em desenvolvimento, tenta Firebase e, como fallback, valida JWT local.
    """
    import logging

    logger = logging.getLogger(__name__)

    if TESTING_MODE:
        logger.info("🔧 Modo de teste ativo - retornando usuário mock")
        return JWTPayload(
            sub="test-user-123",
            role="student",
            tenant="test-tenant",
            exp=9999999999,
            iat=1000000000,
        )

    if not credentials:
        logger.warning("❌ Token não fornecido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {"code": "TOKEN_NOT_PROVIDED", "msg": "Token não fornecido"}
            },
        )

    token = credentials.credentials
    logger.info(f"🔍 Token recebido: {token[:50]}...")
    logger.info(f"🌍 Ambiente: {ENVIRONMENT}")

    if ENVIRONMENT == "production":
        logger.info("🏭 Modo produção - validando apenas com Firebase")
        return await verify_firebase_token(token)

    # Em desenvolvimento, tentar Firebase primeiro, depois JWT local
    logger.info("🔧 Modo desenvolvimento - tentando Firebase primeiro")
    try:
        result = await verify_firebase_token(token)
        logger.info("✅ Token Firebase válido")
        return result
    except HTTPException as e:
        logger.info(f"❌ Firebase falhou: {e.detail}")
        logger.info("🔄 Tentando JWT local como fallback")
        # Se a verificação do Firebase falhar, tente o JWT local
        try:
            result = await verify_local_jwt(token)
            logger.info("✅ Token JWT local válido")
            return result
        except HTTPException as local_e:
            logger.error(f"❌ JWT local também falhou: {local_e.detail}")
            raise local_e


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


async def validate_authenticated_user(
    token: JWTPayload = Depends(get_current_user),
) -> JWTPayload:
    """
    Valida se o usuário está autenticado (qualquer role válida).
    """
    # Se estiver em modo de teste, retornar dados mock
    if TESTING_MODE:
        return JWTPayload(
            sub="test-user-123",
            role="student",
            tenant="test-tenant",
            exp=9999999999,
            iat=1000000000,
        )

    # Verificar se o token tem uma role válida
    valid_roles = ["student", "partner", "admin", "employee"]
    if token.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "INVALID_ROLE",
                    "msg": f"Role '{token.role}' não é válida",
                }
            },
        )

    return token
