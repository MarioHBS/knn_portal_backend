"""Firebase ID-token authentication and role authorization for the API."""

from datetime import datetime
from typing import Any, Literal

import firebase_admin
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth
from pydantic import BaseModel, model_validator

from src.config import FIRESTORE_PROJECT, TESTING_MODE

security = HTTPBearer(auto_error=not TESTING_MODE)
VALID_ROLES = {"admin", "employee", "student", "partner"}


def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK or fail startup outside test mode."""
    if firebase_admin._apps:
        return

    import os
    from pathlib import Path

    from firebase_admin import credentials

    possible_paths = [
        "credentials/default-service-account-key.json",
        "credentials/knn-benefits-service-account-key.json",
        "data/firestore_import/default-service-account-key.json",
        "default-service-account-key.json",
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
    ]

    try:
        cred_path = next(
            (path for path in possible_paths if path and Path(path).exists()), None
        )
        if cred_path:
            firebase_admin.initialize_app(
                credentials.Certificate(cred_path), {"projectId": FIRESTORE_PROJECT}
            )
        else:
            firebase_admin.initialize_app(
                credentials.ApplicationDefault(), {"projectId": FIRESTORE_PROJECT}
            )
    except Exception as exc:
        if not TESTING_MODE:
            raise RuntimeError("Firebase Admin SDK não pôde ser inicializado") from exc
        try:
            firebase_admin.initialize_app(options={"projectId": FIRESTORE_PROJECT})
        except ValueError:
            if not firebase_admin._apps:
                raise


initialize_firebase()


class JWTPayload(BaseModel):
    """Normalized claims from a verified Firebase ID token."""

    sub: str
    role: Literal["admin", "employee", "student", "partner"]
    tenant: str
    entity_id: str | None = None
    exp: int
    iat: int
    iss: str | None = None
    aud: str | list[str] | None = None
    name: str | None = None

    @model_validator(mode="before")
    def exp_must_be_after_iat(cls, data: Any) -> Any:  # noqa: N805
        if isinstance(data, dict):
            iat = data.get("iat")
            exp = data.get("exp")
            if iat is not None and exp is not None and exp <= iat:
                raise ValueError("exp deve ser maior que iat")
        return data

    def expires_iso(self) -> str:
        return datetime.utcfromtimestamp(self.exp).isoformat() + "Z"


def _claims_error(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"error": {"code": code, "msg": message}},
    )


async def extract_data_from_firebase_token(
    token: str, *, check_revoked: bool = False
) -> JWTPayload:
    """Verify a Firebase ID token and normalize its authorization claims."""
    try:
        decoded_token = auth.verify_id_token(token, check_revoked=check_revoked)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_FIREBASE_TOKEN", "msg": str(exc)}},
        ) from exc

    role = decoded_token.get("role")
    if role is None or role == "":
        raise _claims_error("MISSING_ROLE", "O token não contém a role obrigatória")
    if role not in VALID_ROLES:
        raise _claims_error("INVALID_ROLE", f"Role '{role}' não é válida")

    tenant = decoded_token.get("tenant")
    if not isinstance(tenant, str) or not tenant:
        raise _claims_error(
            "MISSING_TENANT", "O token não contém o tenant obrigatório"
        )

    try:
        return JWTPayload(
            sub=decoded_token["uid"],
            role=role,
            tenant=tenant,
            exp=decoded_token["exp"],
            iat=decoded_token["iat"],
            iss=decoded_token.get("iss"),
            aud=decoded_token.get("aud"),
            name=decoded_token.get("name"),
            entity_id=decoded_token.get("entity_id"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_FIREBASE_TOKEN", "msg": str(exc)}},
        ) from exc


def _testing_user() -> JWTPayload:
    return JWTPayload(
        sub="test-user-123",
        role="student",
        tenant="test-tenant",
        exp=9_999_999_999,
        iat=1_000_000_000,
    )


async def _get_current_user(
    authorization: HTTPAuthorizationCredentials | None,
    *,
    check_revoked: bool,
) -> JWTPayload:
    if TESTING_MODE:
        return _testing_user()
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {"code": "TOKEN_NOT_PROVIDED", "msg": "Token não fornecido"}
            },
        )
    return await extract_data_from_firebase_token(
        authorization.credentials, check_revoked=check_revoked
    )


async def get_current_user(
    authorization: HTTPAuthorizationCredentials | None = Security(security),
) -> JWTPayload:
    """Return the authenticated user from a Firebase ID token."""
    return await _get_current_user(authorization, check_revoked=False)


async def get_current_admin_user(
    authorization: HTTPAuthorizationCredentials | None = Security(security),
) -> JWTPayload:
    """Authenticate an admin request with Firebase revocation checking."""
    return await _get_current_user(authorization, check_revoked=True)


def _require_role(token: JWTPayload, role: str, label: str) -> JWTPayload:
    if token.role != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "msg": f"Acesso permitido apenas para {label}",
                }
            },
        )
    return token


async def validate_student_role(
    token: JWTPayload = Depends(get_current_user),
) -> JWTPayload:
    return _require_role(token, "student", "alunos")


async def validate_partner_role(
    token: JWTPayload = Depends(get_current_user),
) -> JWTPayload:
    return _require_role(token, "partner", "parceiros")


async def validate_admin_role(
    token: JWTPayload = Depends(get_current_admin_user),
) -> JWTPayload:
    return _require_role(token, "admin", "administradores")


async def validate_employee_role(
    token: JWTPayload = Depends(get_current_user),
) -> JWTPayload:
    return _require_role(token, "employee", "funcionários")


async def validate_authenticated_user(
    token: JWTPayload = Depends(get_current_user),
) -> JWTPayload:
    """Validate that the token carries one of the supported roles."""
    if token.role not in VALID_ROLES:
        raise _claims_error("INVALID_ROLE", f"Role '{token.role}' não é válida")
    return token
