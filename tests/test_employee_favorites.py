"""
Testes para os endpoints de favoritos dos funcionários.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException


@pytest.fixture
def mock_employee_user():
    """Fixture para usuário funcionário mock."""

    class MockUser:
        def __init__(self):
            self.sub = "employee-123"
            self.email = "employee@test.com"
            self.role = "employee"
            self.tenant_id = "tenant-123"

    return MockUser()


@pytest.fixture
def mock_partner():
    """Fixture para parceiro mock."""

    class MockPartner:
        def __init__(self):
            self.id = "PTN123456"
            self.trade_name = "Parceiro Teste"
            self.active = True
            self.tenant_id = "tenant-123"

    return MockPartner()


class TestEmployeeFavoritesEndpoints:
    """Testes para os endpoints de favoritos do funcionário."""

    @pytest.mark.asyncio
    async def test_get_employee_favorites_success(
        self, mock_employee_user, mock_partner
    ):
        """Testa obtenção de favoritos com sucesso."""
        # Mock do documento de favoritos do funcionário
        mock_employee_favorites = {
            "id": "employee-123",
            "favorites": ["partner-123"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            # Configurar circuit breaker para retornar favoritos e depois parceiro
            mock_circuit_breaker.side_effect = [
                mock_employee_favorites,  # Primeira chamada para obter favoritos
                mock_partner,  # Segunda chamada para obter parceiro
            ]

            from src.api.employee import get_employee_favorites

            result = await get_employee_favorites(mock_employee_user)

            assert result["msg"] == "ok"
            assert len(result["data"]) == 1
            assert result["data"][0].trade_name == "Parceiro Teste"

    @pytest.mark.asyncio
    async def test_get_employee_favorites_empty(self, mock_employee_user):
        """Testa obtenção de favoritos vazio."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker", return_value=None),
        ):
            from src.api.employee import get_employee_favorites

            result = await get_employee_favorites(mock_employee_user)

            assert result["msg"] == "ok"
            assert len(result["data"]) == 0

    @pytest.mark.asyncio
    async def test_add_employee_favorite_success(
        self, mock_employee_user, mock_partner
    ):
        """Testa adição de favorito com sucesso."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
            patch("src.api.employee.firestore_client") as mock_firestore,
        ):
            # Configurar circuit breaker para retornar parceiro e depois None (favoritos não existem)
            mock_circuit_breaker.side_effect = [
                mock_partner,  # Primeira chamada para verificar parceiro
                None,  # Segunda chamada para verificar favoritos (não existe ainda)
            ]
            mock_firestore.create_document = AsyncMock()

            from src.api.employee import add_employee_favorite

            result = await add_employee_favorite(
                {"partner_id": "PTN123456"}, mock_employee_user
            )

            assert result.success is True
            assert "adicionado aos favoritos" in result.message
            mock_firestore.create_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_employee_favorite_already_exists(
        self, mock_employee_user, mock_partner
    ):
        """Testa adição de favorito que já existe."""
        mock_employee_favorites = {
            "id": "employee-123",
            "favorites": ["PTN123456"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker") as mock_circuit_breaker,
        ):
            # Configurar circuit breaker para retornar parceiro e depois favoritos existentes
            mock_circuit_breaker.side_effect = [
                mock_partner,  # Primeira chamada para verificar parceiro
                mock_employee_favorites,  # Segunda chamada para verificar favoritos
            ]

            from src.api.employee import add_employee_favorite

            result = await add_employee_favorite(
                {"partner_id": "PTN123456"}, mock_employee_user
            )

            assert result.success is True
            assert "já está nos favoritos" in result.message

    @pytest.mark.asyncio
    async def test_add_employee_favorite_partner_not_found(self, mock_employee_user):
        """Testa adição de favorito com parceiro não encontrado."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.with_circuit_breaker", return_value=None),
        ):
            from src.api.employee import add_employee_favorite

            with pytest.raises(HTTPException) as exc_info:
                await add_employee_favorite(
                    {"partner_id": "invalid-partner"}, mock_employee_user
                )

            assert exc_info.value.status_code == 404
            assert "NOT_FOUND" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_add_employee_favorite_missing_partner_id(self, mock_employee_user):
        """Testa adição de favorito sem partner_id."""
        with patch(
            "src.api.employee.validate_employee_role", return_value=mock_employee_user
        ):
            from src.api.employee import add_employee_favorite

            with pytest.raises(HTTPException) as exc_info:
                await add_employee_favorite({}, mock_employee_user)

            assert exc_info.value.status_code == 400
            assert "VALIDATION_ERROR" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_remove_employee_favorite_success(self, mock_employee_user):
        """Testa remoção de favorito com sucesso."""
        mock_employee_favorites = {
            "id": "employee-123",
            "favorites": ["PTN123456", "PTN456789"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch(
                "src.api.employee.with_circuit_breaker",
                return_value=mock_employee_favorites,
            ),
            patch("src.api.employee.firestore_client") as mock_firestore,
        ):
            mock_firestore.update_document = AsyncMock()

            from src.api.employee import remove_employee_favorite

            result = await remove_employee_favorite("PTN123456", mock_employee_user)

            assert result.success is True
            assert "removido dos favoritos" in result.message
            mock_firestore.update_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_employee_favorite_not_found(self, mock_employee_user):
        """Testa remoção de favorito não encontrado."""
        mock_employee_favorites = {
            "id": "employee-123",
            "favorites": ["PTN456789"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch(
                "src.api.employee.with_circuit_breaker",
                return_value=mock_employee_favorites,
            ),
        ):
            from src.api.employee import remove_employee_favorite

            with pytest.raises(HTTPException) as exc_info:
                await remove_employee_favorite("PTN123456", mock_employee_user)

            assert exc_info.value.status_code == 404
            assert "NOT_FOUND" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_remove_employee_favorite_last_item(self, mock_employee_user):
        """Testa remoção do último favorito (deve deletar o documento)."""
        mock_employee_favorites = {
            "id": "employee-123",
            "favorites": ["PTN123456"],  # Apenas um favorito
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.return_value = mock_employee_favorites
            mock_firestore.delete_document = AsyncMock()

            from src.api.employee import remove_employee_favorite

            result = await remove_employee_favorite("partner-123", mock_employee_user)

            assert result["msg"] == "ok"
            mock_firestore.delete_document.assert_called_once_with(
                "employees_fav", "employee-123"
            )

    @pytest.mark.asyncio
    async def test_add_employee_favorite_create_new_document(
        self, mock_employee_user, mock_partner
    ):
        """Testa criação de novo documento de favoritos."""
        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.side_effect = [
                mock_partner,  # Primeira chamada para verificar parceiro
                None,  # Segunda chamada para verificar favoritos (não existe)
            ]
            mock_firestore.create_document = AsyncMock()

            from src.api.employee import add_employee_favorite

            result = await add_employee_favorite(
                {"partner_id": "partner-123"}, mock_employee_user
            )

            assert result["msg"] == "ok"

            # Verificar se create_document foi chamado com os dados corretos
            call_args = mock_firestore.create_document.call_args
            assert call_args[1]["collection"] == "employees_fav"
            assert call_args[1]["document_id"] == "employee-123"
            assert "partner-123" in call_args[1]["data"]["favorites"]

    @pytest.mark.asyncio
    async def test_add_employee_favorite_update_existing_document(
        self, mock_employee_user, mock_partner
    ):
        """Testa atualização de documento existente de favoritos."""
        mock_employee_favorites = {
            "id": "employee-123",
            "favorites": ["partner-456"],  # Já tem outro favorito
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with (
            patch(
                "src.api.employee.validate_employee_role",
                return_value=mock_employee_user,
            ),
            patch("src.api.employee.firestore_client") as mock_firestore,
        ):
            mock_firestore.get_document.side_effect = [
                mock_partner,  # Primeira chamada para verificar parceiro
                mock_employee_favorites,  # Segunda chamada para verificar favoritos
            ]
            mock_firestore.update_document = AsyncMock()

            from src.api.employee import add_employee_favorite

            result = await add_employee_favorite(
                {"partner_id": "partner-123"}, mock_employee_user
            )

            assert result["msg"] == "ok"

            # Verificar se update_document foi chamado
            call_args = mock_firestore.update_document.call_args
            assert call_args[0][0] == "employees_fav"  # collection
            assert call_args[0][1] == "employee-123"  # document_id
            assert "partner-123" in call_args[0][2]["favorites"]  # data
            assert "partner-456" in call_args[0][2]["favorites"]  # mantém o existente
