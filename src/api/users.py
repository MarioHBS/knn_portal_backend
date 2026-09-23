"""Authenticated user profile and first-access password endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth import JWTPayload, get_current_user

router = APIRouter(tags=["authentication"])


@router.get("/me")
async def get_me(current_user: JWTPayload = Depends(get_current_user)):
    """Return the authenticated user's profile and first-access state."""
    first_access = True
    entity_id = current_user.entity_id
    try:
        from src.db.firestore import get_database

        db = get_database()
        user_doc = db.collection("users").document(current_user.sub).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            first_access = bool(user_data.get("first_access", True))
            entity_id = user_data.get("entity_id", entity_id)
    except Exception as exc:
        # Profile access must not fail only because optional profile enrichment
        # is unavailable; token claims remain the source of authorization.
        print(f"Aviso: não foi possível enriquecer o perfil do usuário: {exc}")

    return {
        "uid": current_user.sub,
        "role": current_user.role,
        "tenant": current_user.tenant,
        "expires_at": current_user.exp,
        "expires_at_iso": current_user.expires_iso(),
        "first_access": first_access,
        "entity_id": entity_id,
    }


class SetPasswordRequest(BaseModel):
    """Request body for the first-access password change."""

    new_password: str


@router.post("/set-password")
async def set_password(
    request: SetPasswordRequest,
    current_user: JWTPayload = Depends(get_current_user),
):
    """Set the authenticated user's Firebase password and clear first access."""
    try:
        from src.db.firestore import get_database
        from src.utils.auth_service import AuthService

        AuthService().update_password(current_user.sub, request.new_password)
        db = get_database()
        db.collection("users").document(current_user.sub).update(
            {"first_access": False}
        )
        return {"message": "Senha atualizada com sucesso."}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar a senha: {exc}",
        ) from exc
