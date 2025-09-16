"""
Testes unitários para o PartnersService.

Este módulo contém testes para a lógica comum compartilhada
entre os endpoints de listagem de parceiros.
"""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from src.auth import JWTPayload
from src.models import PartnerListResponse
from src.utils.partners_service import PartnersService


@pytest.mark.asyncio
class TestPartnersService:
    """Classe de testes para PartnersService."""

    @pytest_asyncio.fixture
    async def mock_user(self):
        """Fixture para usuário mock."""
        return JWTPayload(
            sub="user123",
            role="student",
            tenant="knn",
            exp=1234567890,
            iat=1234567890,
            iss="test",
            aud="test",
            name="Test User",
        )

    @pytest_asyncio.fixture
    async def mock_partners_data(self):
        """Fixture para dados de parceiros mock."""
        return {
            "items": [
                {
                    "id": "partner-1",
                    "trade_name": "Parceiro A",
                    "category": "alimentacao",
                    "active": True,
                },
                {
                    "id": "partner-2",
                    "trade_name": "Parceiro B",
                    "category": "tecnologia",
                    "active": True,
                },
            ]
        }

    @pytest_asyncio.fixture
    async def mock_empty_data(self):
        """Fixture para dados vazios."""
        return {"items": []}

    async def test_list_partners_common_with_circuit_breaker(
        self, mock_user, mock_partners_data
    ):
        """Testa listagem de parceiros com circuit breaker habilitado."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_partners_data

            result = await PartnersService.list_partners_common(
                current_user=mock_user, use_circuit_breaker=True
            )

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que os dados estão corretos
            assert len(result.data) == 2
            assert result.data[0].id == "partner-1"
            assert result.data[1].id == "partner-2"

            # Verificar que o método correto foi chamado
            mock_query.assert_called_once()

    async def test_list_partners_common_without_circuit_breaker(
        self, mock_user, mock_partners_data
    ):
        """Testa listagem de parceiros sem circuit breaker."""
        with patch.object(
            PartnersService, "_query_firestore_only", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_partners_data

            result = await PartnersService.list_partners_common(
                current_user=mock_user, use_circuit_breaker=False
            )

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que os dados estão corretos
            assert len(result.data) == 2
            assert result.data[0].id == "partner-1"
            assert result.data[1].id == "partner-2"

            # Verificar que o método correto foi chamado
            mock_query.assert_called_once()

    async def test_list_partners_common_with_category_filter(
        self, mock_user, mock_partners_data
    ):
        """Testa listagem de parceiros com filtro de categoria."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_partners_data

            result = await PartnersService.list_partners_common(
                current_user=mock_user, cat="alimentacao", use_circuit_breaker=True
            )

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que os dados estão corretos
            assert len(result.data) == 2

            # Verificar que o método foi chamado com filtros corretos
            call_args = mock_query.call_args[1]
            filters = call_args["filters"]
            assert ("active", "==", True) in filters
            assert ("category", "==", "alimentacao") in filters

    async def test_list_partners_common_with_ordering_name_asc(
        self, mock_user, mock_partners_data
    ):
        """Testa listagem de parceiros com ordenação por nome ascendente."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_partners_data

            result = await PartnersService.list_partners_common(
                current_user=mock_user, ord="name", use_circuit_breaker=True
            )

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que os dados estão corretos
            assert len(result.data) == 2

            # Verificar que o método foi chamado com ordenação correta
            call_args = mock_query.call_args[1]
            order_by = call_args["order_by"]
            assert ("trade_name", "ASCENDING") in order_by

    async def test_list_partners_common_with_ordering_name_desc(
        self, mock_user, mock_partners_data
    ):
        """Testa listagem de parceiros com ordenação por nome descendente."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_partners_data

            result = await PartnersService.list_partners_common(
                current_user=mock_user, ord="name_desc", use_circuit_breaker=True
            )

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que os dados estão corretos
            assert len(result.data) == 2

            # Verificar que o método foi chamado com ordenação correta
            call_args = mock_query.call_args[1]
            order_by = call_args["order_by"]
            assert ("trade_name", "DESCENDING") in order_by

    async def test_list_partners_common_with_ordering_category(
        self, mock_user, mock_partners_data
    ):
        """Testa listagem de parceiros com ordenação por categoria."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_partners_data

            result = await PartnersService.list_partners_common(
                current_user=mock_user, ord="category", use_circuit_breaker=True
            )

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que os dados estão corretos
            assert len(result.data) == 2

            # Verificar que o método foi chamado com ordenação correta
            call_args = mock_query.call_args[1]
            order_by = call_args["order_by"]
            assert ("category", "ASCENDING") in order_by

    async def test_list_partners_common_with_pagination(
        self, mock_user, mock_partners_data
    ):
        """Testa listagem de parceiros com paginação personalizada."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_partners_data

            result = await PartnersService.list_partners_common(
                current_user=mock_user, limit=10, offset=20, use_circuit_breaker=True
            )

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que os dados estão corretos
            assert len(result.data) == 2

            # Verificar que o método foi chamado com paginação correta
            call_args = mock_query.call_args[1]
            assert call_args["limit"] == 10
            assert call_args["offset"] == 20

    async def test_list_partners_common_ordering_disabled(
        self, mock_user, mock_partners_data
    ):
        """Testa listagem de parceiros com ordenação desabilitada."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_partners_data

            result = await PartnersService.list_partners_common(
                current_user=mock_user, enable_ordering=False, use_circuit_breaker=True
            )

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que os dados estão corretos
            assert len(result.data) == 2

            # Verificar que o método foi chamado sem ordenação
            call_args = mock_query.call_args[1]
            order_by = call_args["order_by"]
            assert order_by == []

    async def test_list_partners_common_invalid_ordering(
        self, mock_user, mock_partners_data
    ):
        """Testa listagem de parceiros com ordenação inválida (deve usar padrão)."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_partners_data

            result = await PartnersService.list_partners_common(
                current_user=mock_user, ord="invalid_order", use_circuit_breaker=True
            )

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que os dados estão corretos
            assert len(result.data) == 2

            # Verificar que o método foi chamado com ordenação padrão
            call_args = mock_query.call_args[1]
            order_by = call_args["order_by"]
            assert ("trade_name", "ASCENDING") in order_by

    async def test_list_partners_common_empty_result(self, mock_user, mock_empty_data):
        """Testa listagem de parceiros com resultado vazio."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_empty_data

            result = await PartnersService.list_partners_common(
                current_user=mock_user, use_circuit_breaker=True
            )

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que não há dados
            assert len(result.data) == 0

            # Verificar que o método foi chamado
            mock_query.assert_called_once()

    async def test_list_partners_common_error_handling(self, mock_user):
        """Testa tratamento de erros na listagem de parceiros."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.side_effect = Exception("Erro de conexão")

            with pytest.raises(Exception, match="Erro de conexão"):
                await PartnersService.list_partners_common(
                    current_user=mock_user, use_circuit_breaker=True
                )

    async def test_list_partners_common_default_parameters(
        self, mock_user, mock_partners_data
    ):
        """Testa listagem de parceiros com parâmetros padrão."""
        with patch.object(
            PartnersService, "_query_with_circuit_breaker", new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_partners_data

            result = await PartnersService.list_partners_common(current_user=mock_user)

            # Verificar que o resultado é um PartnerListResponse
            assert isinstance(result, PartnerListResponse)

            # Verificar que os dados estão corretos
            assert len(result.data) == 2

            # Verificar que o método foi chamado com parâmetros padrão
            call_args = mock_query.call_args[1]
            assert call_args["limit"] == 20
            assert call_args["offset"] == 0

            # Verificar filtros padrão
            filters = call_args["filters"]
            assert ("active", "==", True) in filters

            # Verificar ordenação padrão
            order_by = call_args["order_by"]
            assert ("trade_name", "ASCENDING") in order_by

    async def test_query_with_circuit_breaker(self, mock_user, mock_partners_data):
        """Testa método _query_with_circuit_breaker."""
        with patch(
            "src.utils.partners_service.with_circuit_breaker", new_callable=AsyncMock
        ) as mock_circuit_breaker:
            mock_circuit_breaker.return_value = mock_partners_data

            result = await PartnersService._query_with_circuit_breaker(
                current_user=mock_user,
                filters=[("active", "==", True)],
                order_by=[("trade_name", "ASCENDING")],
                limit=20,
                offset=0,
            )

            assert result == mock_partners_data
            mock_circuit_breaker.assert_called_once()

    async def test_query_firestore_only(self, mock_user, mock_partners_data):
        """Testa método _query_firestore_only."""
        with patch("src.utils.partners_service.firestore_client") as mock_firestore:
            mock_firestore.query_documents = AsyncMock(return_value=mock_partners_data)

            result = await PartnersService._query_firestore_only(
                current_user=mock_user,
                filters=[("active", "==", True)],
                order_by=[("trade_name", "ASCENDING")],
                limit=20,
                offset=0,
            )

            assert result == mock_partners_data
            mock_firestore.query_documents.assert_called_once_with(
                "partners",
                tenant_id=mock_user.tenant,
                filters=[("active", "==", True)],
                order_by=[("trade_name", "ASCENDING")],
                limit=20,
                offset=0,
            )

    async def test_query_firestore_only_with_none_order_by(
        self, mock_user, mock_partners_data
    ):
        """Testa método _query_firestore_only com order_by None."""
        with patch("src.utils.partners_service.firestore_client") as mock_firestore:
            mock_firestore.query_documents = AsyncMock(return_value=mock_partners_data)

            result = await PartnersService._query_firestore_only(
                current_user=mock_user,
                filters=[("active", "==", True)],
                order_by=None,
                limit=20,
                offset=0,
            )

            assert result == mock_partners_data
            mock_firestore.query_documents.assert_called_once_with(
                "partners",
                tenant_id=mock_user.tenant,
                filters=[("active", "==", True)],
                order_by=None,
                limit=20,
                offset=0,
            )
