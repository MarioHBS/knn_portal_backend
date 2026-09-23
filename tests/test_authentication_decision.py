"""Regression tests for the Firebase-only authentication decision.

These tests are intentionally written before the implementation described in
stage 004.  They document the fail-closed contract and are expected to fail
against the pre-stage code.
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src import auth as auth_module
from src.api import admin as admin_module
from src.models import EntityType

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _subprocess_environment(extra_environment: dict[str, str]) -> dict[str, str]:
    environment = os.environ.copy()
    for key in ("ENVIRONMENT", "TESTING_MODE", "K_SERVICE"):
        environment.pop(key, None)
    environment.update(extra_environment)
    return environment


def _run_config_import(extra_environment: dict[str, str]) -> subprocess.CompletedProcess:
    """Import config with the repository .env loader disabled."""

    code = """
import sys
import types

dotenv = types.ModuleType("dotenv")
dotenv.load_dotenv = lambda *args, **kwargs: None
sys.modules["dotenv"] = dotenv

import src.config as config
print(config.TESTING_MODE)
"""
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND_ROOT,
        env=_subprocess_environment(extra_environment),
        capture_output=True,
        text=True,
        check=False,
    )


def test_missing_bearer_token_is_rejected_without_environment_flags():
    code = """
import asyncio
from pathlib import Path
import sys
import types

dotenv = types.ModuleType("dotenv")
dotenv.load_dotenv = lambda *args, **kwargs: None
sys.modules["dotenv"] = dotenv

# Avoid src/__init__.py importing every API and initializing external clients.
src_package = types.ModuleType("src")
src_package.__path__ = [str(Path.cwd() / "src")]
sys.modules["src"] = src_package

from fastapi import HTTPException
from src.auth import get_current_user

async def check_authentication():
    try:
        await get_current_user(None)
    except HTTPException as exception:
        print(exception.status_code)
        return
    raise SystemExit("authentication accepted a missing bearer token")

asyncio.run(check_authentication())
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND_ROOT,
        env=_subprocess_environment({}),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith("401")


def _error_code(exception: HTTPException) -> str:
    return exception.detail["error"]["code"]


def _verified_claims(**overrides: object) -> dict[str, object]:
    claims: dict[str, object] = {
        "uid": "firebase-user-123",
        "role": "student",
        "tenant": "tenant-123",
        "entity_id": "student-123",
        "iat": 1_000,
        "exp": 2_000,
    }
    claims.update(overrides)
    return claims


def test_testing_mode_defaults_to_false_without_explicit_environment():
    result = _run_config_import({})

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith("False")


@pytest.mark.parametrize(
    "environment",
    [
        {"TESTING_MODE": "true", "ENVIRONMENT": "test", "K_SERVICE": "backend"},
        {"TESTING_MODE": "false", "K_SERVICE": "backend"},
    ],
    ids=["testing-mode-on-cloud-run", "cloud-run-without-explicit-environment"],
)
def test_unsafe_cloud_run_configuration_aborts_during_import(
    environment: dict[str, str],
):
    result = _run_config_import(environment)

    assert result.returncode != 0


@pytest.mark.asyncio
async def test_firebase_claim_without_role_is_rejected():
    with (
        patch.object(
            auth_module.auth,
            "verify_id_token",
            return_value=_verified_claims(role=None),
        ),
        pytest.raises(HTTPException) as raised,
    ):
        await auth_module.extract_data_from_firebase_token("firebase-token")

    assert raised.value.status_code == 403
    assert _error_code(raised.value) == "MISSING_ROLE"


@pytest.mark.asyncio
async def test_firebase_claim_with_unknown_role_is_rejected():
    with (
        patch.object(
            auth_module.auth,
            "verify_id_token",
            return_value=_verified_claims(role="owner"),
        ),
        pytest.raises(HTTPException) as raised,
    ):
        await auth_module.extract_data_from_firebase_token("firebase-token")

    assert raised.value.status_code == 403
    assert _error_code(raised.value) == "INVALID_ROLE"


@pytest.mark.asyncio
async def test_firebase_claim_without_tenant_is_rejected():
    with (
        patch.object(
            auth_module.auth,
            "verify_id_token",
            return_value=_verified_claims(tenant=None),
        ),
        pytest.raises(HTTPException) as raised,
    ):
        await auth_module.extract_data_from_firebase_token("firebase-token")

    assert raised.value.status_code == 403
    assert _error_code(raised.value) == "MISSING_TENANT"


@pytest.mark.asyncio
async def test_admin_authentication_checks_revoked_tokens(monkeypatch):
    monkeypatch.setattr(auth_module, "TESTING_MODE", False)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="firebase-token"
    )

    with patch.object(
        auth_module.auth,
        "verify_id_token",
        return_value=_verified_claims(),
    ) as verify_id_token:
        user = await auth_module.get_current_admin_user(credentials)

    assert user.sub == "firebase-user-123"
    verify_id_token.assert_called_once_with(
        "firebase-token", check_revoked=True
    )


@pytest.mark.parametrize(
    ("entity", "expected_role"),
    [
        (EntityType.STUDENT, "student"),
        (EntityType.EMPLOYEE, "employee"),
        (EntityType.PARTNER, "partner"),
    ],
)
@pytest.mark.asyncio
async def test_creating_user_sets_firebase_custom_claims(entity, expected_role):
    user_record = MagicMock(uid="firebase-user-123")
    auth_service = MagicMock()
    auth_service.create_user_with_temp_password.return_value = (
        user_record,
        "temporary-password",
    )
    firestore_client = MagicMock()
    firestore_client.create_document = AsyncMock()
    firestore_client.delete_document = AsyncMock()

    with (
        patch.object(admin_module, "AuthService", return_value=auth_service),
        patch.object(admin_module, "auth") as firebase_auth,
        patch.object(admin_module, "firestore_client", firestore_client),
        patch.object(admin_module, "EMAIL_SERVICE_ENABLED", False),
    ):
        await admin_module.create_firebase_user(
            entity=entity,
            entity_name="Entity Example",
            entity_email="entity@example.com",
            entity_id="entity-123",
            tenant_id="tenant-123",
        )

    firebase_auth.set_custom_user_claims.assert_called_once_with(
        "firebase-user-123",
        {
            "role": expected_role,
            "tenant": "tenant-123",
            "entity_id": "entity-123",
        },
    )
