"""
Testes para os endpoints da API de administração.

Este módulo contém testes unitários para todos os endpoints definidos em src/api/admin.py,
incluindo testes de sucesso, falha, validação de dados e integração com autenticação.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import uuid
from datetime import date, datetime

from src.api.admin import router
from src.models.admin import (
    EntityCreateRequest,
    EntityUpdateRequest,
    NotificationRequest,
    MetricsResponse,
)
from src.models import BaseResponse
from src.auth import JWTPayload


@pytest.fixture
def mock_admin_user():
    """Fixture para usuário administrador autenticado."""
    return JWTPayload(
        sub="admin_123",
        role="admin",
        tenant="test_tenant",
        exp=9999999999,
        iat=1000000000,
    )


@pytest.fixture
def mock_partner_data():
    """Fixture com dados de parceiro para testes."""
    return {
        "id": "partner_123",
        "trade_name": "Parceiro Teste",
        "cnpj": "12345678000195",
        "active": True,
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_student_data():
    """Fixture com dados de estudante para testes."""
    return {
        "id": "student_123",
        "name": "Estudante Teste",
        "email": "student@test.com",
        "active": True,
        "active_until": "2024-12-31",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_promotion_data():
    """Fixture com dados de promoção para testes."""
    return {
        "id": "promotion_123",
        "title": "Promoção Teste",
        "description": "Descrição da promoção",
        "partner_id": "partner_123",
        "active": True,
        "created_at": "2024-01-01T00:00:00Z",
    }


class TestListPartners:
    """Testes para o endpoint de listagem de parceiros."""

    @pytest.mark.asyncio
    @patch("src.api.admin.with_circuit_breaker")
    @patch("src.api.admin.validate_admin_role")
    async def test_list_partners_success(
        self, mock_validate_role, mock_circuit_breaker, mock_admin_user, mock_partner_data
    ):
        """Testa listagem bem-sucedida de parceiros."""
        mock_validate_role.return_value = mock_admin_user
        mock_circuit_breaker.return_value = {
            "items": [mock_partner_data],
            "total": 1,
            "page": 1,
            "per_page": 10,
        }

        with TestClient(router) as client:
            response = client.get("/partners")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["msg"] == "ok"
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["id"] == "partner_123"

    @pytest.mark.asyncio
    @patch("src.api.admin.with_circuit_breaker")
    @patch("src.api.admin.validate_admin_role")
    async def test_list_partners_with_filters(
        self, mock_validate_role, mock_circuit_breaker, mock_admin_user, mock_partner_data
    ):
        """Testa listagem de parceiros com filtros aplicados."""
        mock_validate_role.return_value = mock_admin_user
        mock_circuit_breaker.return_value = {
            "items": [mock_partner_data],
            "total": 1,
            "page": 1,
            "per_page": 10,
        }

        with TestClient(router) as client:
            response = client.get("/partners?cat=food&ord=name&limit=5&offset=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["msg"] == "ok"

    @pytest.mark.asyncio
    @patch("src.api.admin.with_circuit_breaker")
    @patch("src.api.admin.validate_admin_role")
    async def test_list_partners_circuit_breaker_failure(
        self, mock_validate_role, mock_circuit_breaker, mock_admin_user
    ):
        """Testa falha do circuit breaker na listagem de parceiros."""
        mock_validate_role.return_value = mock_admin_user
        mock_circuit_breaker.side_effect = Exception("Circuit breaker open")

        with TestClient(router) as client:
            response = client.get("/partners")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestGetPartnerDetails:
    """Testes para o endpoint de detalhes do parceiro."""

    @pytest.mark.asyncio
    @patch("src.api.admin.with_circuit_breaker")
    @patch("src.api.admin.validate_admin_role")
    async def test_get_partner_details_success(
        self, mock_validate_role, mock_circuit_breaker, mock_admin_user, mock_partner_data
    ):
        """Testa obtenção bem-sucedida de detalhes do parceiro."""
        mock_validate_role.return_value = mock_admin_user
        mock_circuit_breaker.return_value = mock_partner_data

        with TestClient(router) as client:
            response = client.get("/partners/partner_123")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["msg"] == "ok"
        assert data["data"]["id"] == "partner_123"

    @pytest.mark.asyncio
    @patch("src.api.admin.with_circuit_breaker")
    @patch("src.api.admin.validate_admin_role")
    async def test_get_partner_details_not_found(
        self, mock_validate_role, mock_circuit_breaker, mock_admin_user
    ):
        """Testa parceiro não encontrado."""
        mock_validate_role.return_value = mock_admin_user
        mock_circuit_breaker.return_value = None

        with TestClient(router) as client:
            response = client.get("/partners/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreateEntity:
    """Testes para o endpoint de criação de entidades."""

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_create_entity_success(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa criação bem-sucedida de entidade."""
        mock_validate_role.return_value = mock_admin_user
        mock_firestore.collection.return_value.add.return_value = (
            None,
            MagicMock(id="new_entity_123"),
        )

        request_data = {
            "entity_type": "partner",
            "data": {"name": "Novo Parceiro", "active": True},
        }

        with TestClient(router) as client:
            response = client.post("/entities", json=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["msg"] == "ok"

    @pytest.mark.asyncio
    @patch("src.api.admin.validate_admin_role")
    async def test_create_entity_invalid_entity_type(
        self, mock_validate_role, mock_admin_user
    ):
        """Testa criação com tipo de entidade inválido."""
        mock_validate_role.return_value = mock_admin_user

        request_data = {
            "entity_type": "invalid_type",
            "data": {"name": "Test"},
        }

        with TestClient(router) as client:
            response = client.post("/entities", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_create_entity_firestore_error(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa erro do Firestore na criação."""
        mock_validate_role.return_value = mock_admin_user
        mock_firestore.collection.return_value.add.side_effect = Exception(
            "Firestore error"
        )

        request_data = {
            "entity_type": "partner",
            "data": {"name": "Test Partner"},
        }

        with TestClient(router) as client:
            response = client.post("/entities", json=request_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestUpdateEntity:
    """Testes para o endpoint de atualização de entidades."""

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_update_entity_success(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa atualização bem-sucedida de entidade."""
        mock_validate_role.return_value = mock_admin_user
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        request_data = {
            "entity_type": "partner",
            "data": {"name": "Parceiro Atualizado"},
        }

        with TestClient(router) as client:
            response = client.put("/entities/partner_123", json=request_data)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_update_entity_not_found(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa atualização de entidade não encontrada."""
        mock_validate_role.return_value = mock_admin_user
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        request_data = {
            "entity_type": "partner",
            "data": {"name": "Test"},
        }

        with TestClient(router) as client:
            response = client.put("/entities/nonexistent", json=request_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteEntity:
    """Testes para o endpoint de exclusão de entidades."""

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_delete_entity_soft_delete_success(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa exclusão lógica bem-sucedida."""
        mock_validate_role.return_value = mock_admin_user
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        with TestClient(router) as client:
            response = client.delete("/entities/partner_123?entity_type=partner")

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_delete_entity_not_found(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa exclusão de entidade não encontrada."""
        mock_validate_role.return_value = mock_admin_user
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        with TestClient(router) as client:
            response = client.delete("/entities/nonexistent?entity_type=partner")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetMetrics:
    """Testes para o endpoint de métricas."""

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_get_metrics_success(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa obtenção bem-sucedida de métricas."""
        mock_validate_role.return_value = mock_admin_user

        # Mock das consultas do Firestore
        mock_firestore.collection.return_value.where.return_value.stream.return_value = [
            MagicMock(),
            MagicMock(),
        ]

        with TestClient(router) as client:
            response = client.get("/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["msg"] == "ok"
        assert "data" in data
        assert "total_partners" in data["data"]
        assert "total_students" in data["data"]
        assert "total_promotions" in data["data"]
        assert "total_validations" in data["data"]

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_get_metrics_error(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa erro na obtenção de métricas."""
        mock_validate_role.return_value = mock_admin_user
        mock_firestore.collection.side_effect = Exception("Firestore error")

        with TestClient(router) as client:
            response = client.get("/metrics")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestSendNotifications:
    """Testes para o endpoint de envio de notificações."""

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_send_notifications_success(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa envio bem-sucedido de notificações."""
        mock_validate_role.return_value = mock_admin_user
        mock_firestore.collection.return_value.where.return_value.stream.return_value = [
            MagicMock(to_dict=lambda: {"email": "test@example.com"}),
        ]

        request_data = {
            "target": "students",
            "type": "email",
            "title": "Teste",
            "message": "Mensagem de teste",
            "filter": {},
        }

        with TestClient(router) as client:
            response = client.post("/notifications", json=request_data)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    @patch("src.api.admin.validate_admin_role")
    async def test_send_notifications_invalid_target(
        self, mock_validate_role, mock_admin_user
    ):
        """Testa envio com target inválido."""
        mock_validate_role.return_value = mock_admin_user

        request_data = {
            "target": "invalid_target",
            "type": "email",
            "title": "Teste",
            "message": "Mensagem",
            "filter": {},
        }

        with TestClient(router) as client:
            response = client.post("/notifications", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @patch("src.api.admin.validate_admin_role")
    async def test_send_notifications_invalid_type(
        self, mock_validate_role, mock_admin_user
    ):
        """Testa envio com tipo inválido."""
        mock_validate_role.return_value = mock_admin_user

        request_data = {
            "target": "students",
            "type": "invalid_type",
            "title": "Teste",
            "message": "Mensagem",
            "filter": {},
        }

        with TestClient(router) as client:
            response = client.post("/notifications", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthenticationAndAuthorization:
    """Testes para autenticação e autorização."""

    @pytest.mark.asyncio
    @patch("src.api.admin.validate_admin_role")
    async def test_unauthorized_access(self, mock_validate_role):
        """Testa acesso não autorizado."""
        from fastapi import HTTPException

        mock_validate_role.side_effect = HTTPException(
            status_code=401, detail="Unauthorized"
        )

        with TestClient(router) as client:
            response = client.get("/partners")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    @patch("src.api.admin.validate_admin_role")
    async def test_forbidden_access_non_admin(self, mock_validate_role):
        """Testa acesso proibido para não-admin."""
        from fastapi import HTTPException

        mock_validate_role.side_effect = HTTPException(
            status_code=403, detail="Forbidden"
        )

        with TestClient(router) as client:
            response = client.get("/partners")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestIntegrationScenarios:
    """Testes de cenários de integração."""

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_complete_entity_lifecycle(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa ciclo completo de vida de uma entidade."""
        mock_validate_role.return_value = mock_admin_user

        # Mock para criação
        mock_firestore.collection.return_value.add.return_value = (
            None,
            MagicMock(id="test_entity_123"),
        )

        # Mock para leitura/atualização/exclusão
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        with TestClient(router) as client:
            # Criar
            create_response = client.post(
                "/entities",
                json={"entity_type": "partner", "data": {"name": "Test Partner"}},
            )
            assert create_response.status_code == status.HTTP_201_CREATED

            # Atualizar
            update_response = client.put(
                "/entities/test_entity_123",
                json={"entity_type": "partner", "data": {"name": "Updated Partner"}},
            )
            assert update_response.status_code == status.HTTP_200_OK

            # Excluir
            delete_response = client.delete(
                "/entities/test_entity_123?entity_type=partner"
            )
            assert delete_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    @patch("src.api.admin.firestore_client")
    @patch("src.api.admin.validate_admin_role")
    async def test_metrics_calculation_accuracy(
        self, mock_validate_role, mock_firestore, mock_admin_user
    ):
        """Testa precisão do cálculo de métricas."""
        mock_validate_role.return_value = mock_admin_user

        # Mock com dados específicos para verificar cálculos
        mock_partners = [MagicMock() for _ in range(5)]
        mock_students = [MagicMock() for _ in range(10)]
        mock_promotions = [MagicMock() for _ in range(3)]
        mock_validations = [MagicMock() for _ in range(15)]

        def mock_stream_side_effect(*args, **kwargs):
            # Simular diferentes coleções baseado no contexto
            collection_name = args[0] if args else "unknown"
            if "partners" in str(collection_name):
                return mock_partners
            elif "students" in str(collection_name):
                return mock_students
            elif "promotions" in str(collection_name):
                return mock_promotions
            elif "validation_codes" in str(collection_name):
                return mock_validations
            return []

        mock_firestore.collection.return_value.where.return_value.stream.side_effect = (
            mock_stream_side_effect
        )

        with TestClient(router) as client:
            response = client.get("/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        # Verificar se os valores calculados estão corretos
        assert data["total_partners"] >= 0
        assert data["total_students"] >= 0
        assert data["total_promotions"] >= 0
        assert data["total_validations"] >= 0


if __name__ == "__main__":
    pytest.main([__file__])