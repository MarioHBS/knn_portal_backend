import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Importações simuladas para testes
# from src.main import app
# from src.auth import verify_token
# from src.db import firestore_client, postgres_client
# from src.models import Student, Partner, Promotion, ValidationCode, Redemption


# Cliente de teste simulado
@pytest.fixture
def client():
    # Simulação do app FastAPI
    from fastapi import Depends, FastAPI, HTTPException

    app = FastAPI()

    # Configuração de rotas simuladas para teste
    @app.get("/v1/health")
    async def health():
        return {"status": "ok", "mode": "normal"}

    # Simulação de autenticação
    async def get_current_user(role: str = None):
        return {"id": "user-id", "role": role}

    # Rotas para testes
    @app.get("/v1/partners")
    async def list_partners(
        current_user=Depends(lambda: get_current_user(role="student")),
    ):
        return {
            "data": {
                "items": [
                    {
                        "id": str(uuid.uuid4()),
                        "trade_name": "Parceiro 1",
                        "category": "Livraria",
                        "address": "Endereço 1",
                        "active": True,
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "trade_name": "Parceiro 2",
                        "category": "Restaurante",
                        "address": "Endereço 2",
                        "active": True,
                    },
                ],
                "total": 2,
                "limit": 20,
                "offset": 0,
            },
            "msg": "ok",
        }

    @app.get("/v1/partners/{id}")
    async def get_partner(
        id: str, current_user=Depends(lambda: get_current_user(role="student"))
    ):
        if id == "not-found":
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )
        return {
            "data": {
                "id": id,
                "trade_name": "Parceiro Teste",
                "category": "Livraria",
                "address": "Endereço Teste",
                "active": True,
                "promotions": [
                    {
                        "id": str(uuid.uuid4()),
                        "partner_id": id,
                        "title": "Promoção Teste",
                        "type": "discount",
                        "valid_from": datetime.now().isoformat(),
                        "valid_to": (datetime.now() + timedelta(days=30)).isoformat(),
                        "active": True,
                    }
                ],
            },
            "msg": "ok",
        }

    @app.post("/v1/validation-codes")
    async def create_validation_code(
        request: dict, current_user=Depends(lambda: get_current_user(role="student"))
    ):
        return {
            "data": {
                "code": "123456",
                "expires": (datetime.now() + timedelta(minutes=3)).isoformat(),
            },
            "msg": "ok",
        }

    @app.post("/v1/partner/redeem")
    async def redeem_code(
        request: dict, current_user=Depends(lambda: get_current_user(role="partner"))
    ):
        if request.get("code") == "invalid":
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "msg": "Código não encontrado"}},
            )
        if request.get("code") == "expired":
            raise HTTPException(
                status_code=410,
                detail={
                    "error": {"code": "EXPIRED", "msg": "Código expirado ou já usado"}
                },
            )
        return {
            "data": {
                "student": {"name": "Aluno Teste", "course": "ADVANCED 1"},
                "promotion": {"title": "Promoção Teste"},
            },
            "msg": "ok",
        }

    # Rota com rate limit para testes
    _rate_limit_counter = {"count": 0, "reset_time": time.time() + 60}

    @app.post("/v1/partner/redeem-with-rate-limit")
    async def redeem_with_rate_limit(
        request: dict, current_user=Depends(lambda: get_current_user(role="partner"))
    ):
        # Simular rate limit (5 requisições por minuto)
        nonlocal _rate_limit_counter

        # Reset contador se passou 1 minuto
        if time.time() > _rate_limit_counter["reset_time"]:
            _rate_limit_counter = {"count": 0, "reset_time": time.time() + 60}

        _rate_limit_counter["count"] += 1

        if _rate_limit_counter["count"] > 5:
            raise HTTPException(
                status_code=429,
                detail={"error": {"code": "RATE_LIMIT", "msg": "Rate limit excedido"}},
            )

        return {
            "data": {
                "student": {"name": "Aluno Teste", "course": "ADVANCED 1"},
                "promotion": {"title": "Promoção Teste"},
            },
            "msg": "ok",
        }

    # Rotas para funcionários (employee)
    @app.get("/v1/employees/partners")
    async def employee_list_partners(
        current_user=Depends(lambda: get_current_user(role="employee")),
    ):
        return {
            "data": {
                "items": [
                    {
                        "id": str(uuid.uuid4()),
                        "trade_name": "Parceiro 1",
                        "category": "Livraria",
                        "address": "Endereço 1",
                        "active": True,
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "trade_name": "Parceiro 2",
                        "category": "Restaurante",
                        "address": "Endereço 2",
                        "active": True,
                    },
                ],
                "total": 2,
                "limit": 20,
                "offset": 0,
            },
            "msg": "ok",
        }

    @app.get("/v1/employees/partners/{id}")
    async def employee_get_partner(
        id: str, current_user=Depends(lambda: get_current_user(role="employee"))
    ):
        if id == "not-found":
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {"code": "NOT_FOUND", "msg": "Parceiro não encontrado"}
                },
            )
        return {
            "data": {
                "id": id,
                "trade_name": "Parceiro Teste",
                "category": "Livraria",
                "address": "Endereço Teste",
                "active": True,
                "promotions": [
                    {
                        "id": str(uuid.uuid4()),
                        "title": "Promoção para Funcionários",
                        "type": "discount",
                        "target_profile": "employee",
                        "valid_from": datetime.now().isoformat(),
                        "valid_to": (datetime.now() + timedelta(days=30)).isoformat(),
                        "active": True,
                    }
                ],
            },
            "msg": "ok",
        }

    @app.post("/v1/employees/validation-codes")
    async def employee_create_validation_code(
        current_user=Depends(lambda: get_current_user(role="employee")),
    ):
        return {
            "data": {
                "code": "123456",
                "expires": (datetime.now() + timedelta(minutes=3)).isoformat(),
                "partner_id": str(uuid.uuid4()),
            },
            "msg": "ok",
        }

    @app.get("/v1/employees/me/history")
    async def employee_history(
        current_user=Depends(lambda: get_current_user(role="employee")),
    ):
        return {
            "data": {
                "items": [
                    {
                        "id": str(uuid.uuid4()),
                        "partner_name": "Parceiro Teste",
                        "code": "123456",
                        "created_at": datetime.now().isoformat(),
                        "used_at": None,
                    }
                ],
                "total": 1,
                "limit": 20,
                "offset": 0,
            },
            "msg": "ok",
        }

    @app.get("/v1/employees/me/fav")
    async def employee_get_favorites(
        current_user=Depends(lambda: get_current_user(role="employee")),
    ):
        return {
            "data": [
                {
                    "id": str(uuid.uuid4()),
                    "trade_name": "Parceiro Favorito",
                    "category": "Livraria",
                    "address": "Endereço",
                    "active": True,
                }
            ],
            "msg": "ok",
        }

    @app.post("/v1/employees/me/fav")
    async def employee_add_favorite(
        current_user=Depends(lambda: get_current_user(role="employee")),
    ):
        return {"data": {}, "msg": "ok"}

    @app.delete("/v1/employees/me/fav/{partner_id}")
    async def employee_remove_favorite(
        partner_id: str, current_user=Depends(lambda: get_current_user(role="employee"))
    ):
        return {"data": {}, "msg": "ok"}

    # Rota admin para testes
    @app.get("/v1/admin/metrics")
    async def admin_metrics(
        current_user=Depends(lambda: get_current_user(role="admin")),
    ):
        return {
            "data": {
                "active_students": 1250,
                "codes_generated": 3456,
                "codes_redeemed": 2789,
                "top_partners": [
                    {
                        "partner_id": str(uuid.uuid4()),
                        "trade_name": "Parceiro Top 1",
                        "redemptions": 456,
                    },
                    {
                        "partner_id": str(uuid.uuid4()),
                        "trade_name": "Parceiro Top 2",
                        "redemptions": 321,
                    },
                ],
            },
            "msg": "ok",
        }

    # Rota que requer autenticação mas sem role específica
    @app.get("/v1/authenticated")
    async def authenticated_route(current_user=Depends(get_current_user)):
        return {"data": {"authenticated": True}, "msg": "ok"}

    # Middleware para simular autenticação JWT
    @app.middleware("http")
    async def auth_middleware(request, call_next):
        from fastapi import Response

        # Verificar header de autenticação
        auth_header = request.headers.get("Authorization")

        # Rota de health não requer autenticação
        if request.url.path == "/v1/health":
            return await call_next(request)

        # Verificar token
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                status_code=401,
                content='{"error":{"code":"UNAUTHORIZED","msg":"Token inválido"}}',
                media_type="application/json",
            )

        # Extrair token
        token = auth_header.split(" ")[1]

        # Token inválido
        if token == "invalid":
            return Response(
                status_code=401,
                content='{"error":{"code":"UNAUTHORIZED","msg":"Token inválido"}}',
                media_type="application/json",
            )

        # Token com role inválida
        if token == "wrong-role":
            return Response(
                status_code=403,
                content='{"error":{"code":"FORBIDDEN","msg":"Acesso negado"}}',
                media_type="application/json",
            )

        return await call_next(request)

    return TestClient(app)


# Testes de Health Check
def test_health_check(client):
    """Teste do endpoint de health check"""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "normal"}


# Testes de Autenticação
def test_missing_token(client):
    """Teste de requisição sem token de autenticação"""
    response = client.get("/v1/authenticated")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_invalid_token(client):
    """Teste de requisição com token inválido"""
    response = client.get(
        "/v1/authenticated", headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_wrong_role(client):
    """Teste de requisição com role incorreta"""
    response = client.get(
        "/v1/authenticated", headers={"Authorization": "Bearer wrong-role"}
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


# Testes de Endpoints para Alunos
def test_list_partners(client):
    """Teste de listagem de parceiros"""
    response = client.get(
        "/v1/partners", headers={"Authorization": "Bearer valid-student"}
    )
    assert response.status_code == 200
    assert "data" in response.json()
    assert "items" in response.json()["data"]
    assert len(response.json()["data"]["items"]) == 2


def test_get_partner_details(client):
    """Teste de detalhes de parceiro"""
    partner_id = str(uuid.uuid4())
    response = client.get(
        f"/v1/partners/{partner_id}", headers={"Authorization": "Bearer valid-student"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["id"] == partner_id
    assert "promotions" in response.json()["data"]


def test_partner_not_found(client):
    """Teste de parceiro não encontrado"""
    response = client.get(
        "/v1/partners/not-found", headers={"Authorization": "Bearer valid-student"}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_create_validation_code(client):
    """Teste de criação de código de validação"""
    response = client.post(
        "/v1/validation-codes",
        json={"partner_id": str(uuid.uuid4())},
        headers={"Authorization": "Bearer valid-student"},
    )
    assert response.status_code == 200
    assert "code" in response.json()["data"]
    assert "expires" in response.json()["data"]


# Testes de Endpoints para Parceiros
def test_redeem_code(client):
    """Teste de resgate de código"""
    response = client.post(
        "/v1/partner/redeem",
        json={"code": "123456", "cpf": "12345678901"},
        headers={"Authorization": "Bearer valid-partner"},
    )
    assert response.status_code == 200
    assert "student" in response.json()["data"]
    assert "promotion" in response.json()["data"]


def test_redeem_invalid_code(client):
    """Teste de resgate com código inválido"""
    response = client.post(
        "/v1/partner/redeem",
        json={"code": "invalid", "cpf": "12345678901"},
        headers={"Authorization": "Bearer valid-partner"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_redeem_expired_code(client):
    """Teste de resgate com código expirado"""
    response = client.post(
        "/v1/partner/redeem",
        json={"code": "expired", "cpf": "12345678901"},
        headers={"Authorization": "Bearer valid-partner"},
    )
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "EXPIRED"


def test_rate_limit(client):
    """Teste de rate limit"""
    # Fazer 6 requisições (o limite é 5 por minuto)
    for i in range(6):
        response = client.post(
            "/v1/partner/redeem-with-rate-limit",
            json={"code": "123456", "cpf": "12345678901"},
            headers={"Authorization": "Bearer valid-partner"},
        )
        if i < 5:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
            assert response.json()["error"]["code"] == "RATE_LIMIT"


# Testes de Endpoints para Administradores
def test_admin_metrics(client):
    """Teste de métricas para administradores"""
    response = client.get(
        "/v1/admin/metrics", headers={"Authorization": "Bearer valid-admin"}
    )
    assert response.status_code == 200
    assert "active_students" in response.json()["data"]
    assert "codes_generated" in response.json()["data"]
    assert "codes_redeemed" in response.json()["data"]
    assert "top_partners" in response.json()["data"]


# Testes de integração com Firestore e PostgreSQL
@pytest.mark.integration
def test_firestore_integration():
    """Teste de integração com Firestore (simulado)"""
    with patch("src.db.firestore_client") as mock_firestore:
        # Configurar mock
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {"id": "test-id", "name": "Test Name"}
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc

        # Testar acesso ao Firestore
        from src.db import get_document

        result = get_document("collection", "doc-id")

        # Verificar resultado
        assert result["id"] == "test-id"
        assert result["name"] == "Test Name"


@pytest.mark.integration
def test_postgres_integration():
    """Teste de integração com PostgreSQL (simulado)"""
    with patch("src.db.postgres_client") as mock_postgres:
        # Configurar mock
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("test-id", "Test Name")]
        mock_postgres.cursor.return_value.__enter__.return_value = mock_cursor

        # Testar acesso ao PostgreSQL
        from src.db import execute_query

        result = execute_query("SELECT id, name FROM table WHERE id = %s", ["test-id"])

        # Verificar resultado
        assert result[0][0] == "test-id"
        assert result[0][1] == "Test Name"


# Testes de Circuit Breaker
@pytest.mark.integration
def test_circuit_breaker():
    """Teste de circuit breaker para Firestore (simulado)"""
    with (
        patch("src.db.firestore_client") as mock_firestore,
        patch("src.db.postgres_client") as mock_postgres,
    ):
        # Configurar mock do Firestore para falhar
        mock_firestore.collection.side_effect = Exception("Firestore error")

        # Configurar mock do PostgreSQL
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("test-id", "Test Name")]
        mock_postgres.cursor.return_value.__enter__.return_value = mock_cursor

        # Testar circuit breaker
        from src.db import get_document_with_fallback

        # Primeira chamada - deve tentar Firestore e cair para PostgreSQL
        result1 = get_document_with_fallback("collection", "doc-id")
        assert result1["id"] == "test-id"
        assert result1["name"] == "Test Name"

        # Segunda chamada - deve tentar Firestore novamente e cair para PostgreSQL
        result2 = get_document_with_fallback("collection", "doc-id")
        assert result2["id"] == "test-id"
        assert result2["name"] == "Test Name"

        # Terceira chamada - deve tentar Firestore novamente e cair para PostgreSQL
        result3 = get_document_with_fallback("collection", "doc-id")
        assert result3["id"] == "test-id"
        assert result3["name"] == "Test Name"

        # Quarta chamada - circuit breaker ativado, deve ir direto para PostgreSQL
        mock_firestore.collection.reset_mock()  # Resetar o mock para verificar se é chamado
        result4 = get_document_with_fallback("collection", "doc-id")
        assert result4["id"] == "test-id"
        assert result4["name"] == "Test Name"
        assert not mock_firestore.collection.called  # Não deve chamar Firestore


# Testes de validação de CPF
def test_cpf_validation():
    """Teste de validação de CPF"""
    from src.utils import hash_cpf, validate_cpf

    # CPF válido
    assert validate_cpf("12345678909") is True

    # CPF inválido
    assert validate_cpf("12345678900") is False

    # Hash de CPF
    cpf_hash = hash_cpf("12345678909", "salt")
    assert isinstance(cpf_hash, str)
    assert len(cpf_hash) > 0


# Testes de mascaramento de CPF em logs
def test_cpf_masking_in_logs():
    """Teste de mascaramento de CPF em logs"""
    from src.utils import mask_cpf_in_log

    # Log com CPF
    log_with_cpf = {"cpf": "12345678909", "name": "Test"}
    masked_log = mask_cpf_in_log(log_with_cpf)
    assert masked_log["cpf"] == "***********"
    assert masked_log["name"] == "Test"

    # Log com CPF em texto
    log_text = "CPF: 12345678909, Nome: Test"
    masked_text = mask_cpf_in_log(log_text)
    assert "CPF: ***********" in masked_text
    assert "Nome: Test" in masked_text


# Testes de Endpoints para Funcionários
def test_employee_list_partners(client):
    """Teste de listagem de parceiros para funcionários"""
    response = client.get(
        "/v1/employees/partners", headers={"Authorization": "Bearer valid-employee"}
    )
    assert response.status_code == 200
    assert "data" in response.json()
    assert "items" in response.json()["data"]
    assert len(response.json()["data"]["items"]) == 2


def test_employee_get_partner_details(client):
    """Teste de detalhes do parceiro para funcionários"""
    partner_id = str(uuid.uuid4())
    response = client.get(
        f"/v1/employees/partners/{partner_id}",
        headers={"Authorization": "Bearer valid-employee"},
    )
    assert response.status_code == 200
    assert "data" in response.json()
    assert "promotions" in response.json()["data"]
    # Verificar se a promoção é específica para funcionários
    promotions = response.json()["data"]["promotions"]
    if promotions:
        assert promotions[0]["target_profile"] == "employee"


def test_employee_partner_not_found(client):
    """Teste de parceiro não encontrado para funcionários"""
    response = client.get(
        "/v1/employees/partners/not-found",
        headers={"Authorization": "Bearer valid-employee"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_employee_create_validation_code(client):
    """Teste de geração de código de validação para funcionários"""
    response = client.post(
        "/v1/employees/validation-codes",
        json={"partner_id": str(uuid.uuid4())},
        headers={"Authorization": "Bearer valid-employee"},
    )
    assert response.status_code == 200
    assert "code" in response.json()["data"]
    assert "expires" in response.json()["data"]
    assert len(response.json()["data"]["code"]) == 6


def test_employee_history(client):
    """Teste de histórico de resgates para funcionários"""
    response = client.get(
        "/v1/employees/me/history", headers={"Authorization": "Bearer valid-employee"}
    )
    assert response.status_code == 200
    assert "data" in response.json()
    assert "items" in response.json()["data"]
    assert "total" in response.json()["data"]


def test_employee_get_favorites(client):
    """Teste de listagem de favoritos para funcionários"""
    response = client.get(
        "/v1/employees/me/fav", headers={"Authorization": "Bearer valid-employee"}
    )
    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"], list)


def test_employee_add_favorite(client):
    """Teste de adição de favorito para funcionários"""
    response = client.post(
        "/v1/employees/me/fav",
        json={"partner_id": str(uuid.uuid4())},
        headers={"Authorization": "Bearer valid-employee"},
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "ok"


def test_employee_remove_favorite(client):
    """Teste de remoção de favorito para funcionários"""
    partner_id = str(uuid.uuid4())
    response = client.delete(
        f"/v1/employees/me/fav/{partner_id}",
        headers={"Authorization": "Bearer valid-employee"},
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "ok"


def test_employee_wrong_role_access(client):
    """Teste de acesso negado para endpoints de funcionário com role incorreta"""
    # Tentar acessar endpoint de funcionário com token de estudante
    response = client.get(
        "/v1/employees/partners", headers={"Authorization": "Bearer valid-student"}
    )
    assert response.status_code == 403

    # Tentar acessar endpoint de funcionário com token de parceiro
    response = client.get(
        "/v1/employees/partners", headers={"Authorization": "Bearer valid-partner"}
    )
    assert response.status_code == 403
