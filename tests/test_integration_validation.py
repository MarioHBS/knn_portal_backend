"""
Testes de integração para validação de dados e comunicação frontend-backend.

Este módulo contém testes que validam:
- Comunicação entre frontend e backend
- Validação de dados nos endpoints
- Fluxos completos de funcionalidades
- Consistência de tipos entre frontend e backend
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.auth import JWTPayload
from src.main import app
from src.models import (
    Benefit,
    BenefitConfiguration,
    BenefitLimits,
    EmployeeFavorites,
    FavoriteRequest,
    Partner,
    PartnerAddress,
    PartnerSocialNetworks,
    StudentFavorites,
)


@pytest.fixture
def client():
    """Cliente de teste FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_student_user():
    """Fixture para usuário estudante mock."""
    return JWTPayload(
        sub="STD_A3C1M7L7_S4",
        role="student",
        tenant="knn",
        exp=int((datetime.now() + timedelta(hours=1)).timestamp()),
        iat=int(datetime.now().timestamp()),
        iss="test",
        aud="test",
        name="Test Student",
    )


@pytest.fixture
def mock_employee_user():
    """Fixture para usuário funcionário mock."""
    return JWTPayload(
        sub="EMP_A0A0O007_AP",
        role="employee",
        tenant="knn",
        exp=int((datetime.now() + timedelta(hours=1)).timestamp()),
        iat=int(datetime.now().timestamp()),
        iss="test",
        aud="test",
        name="Test Employee",
    )


@pytest.fixture
def sample_partner():
    """Fixture para parceiro de exemplo."""
    return Partner(
        id="partner-123",
        tenant_id="knn",
        trade_name="Restaurante Teste",
        legal_name="Restaurante Teste LTDA",
        cnpj="12.345.678/0001-90",
        category="alimentacao",
        description="Restaurante especializado em comida brasileira",
        address=PartnerAddress(
            street="Rua das Flores, 123",
            neighborhood="Centro",
            city="São Paulo",
            state="SP",
            zip_code="01234-567",
            country="Brasil"
        ),
        contact_phone="(11) 1234-5678",
        contact_email="contato@restauranteteste.com.br",
        website="https://restauranteteste.com.br",
        social_networks=PartnerSocialNetworks(
            instagram="@restauranteteste",
            facebook="restauranteteste",
            twitter="@restteste"
        ),
        logo_url="https://example.com/logo.png",
        banner_url="https://example.com/banner.png",
        active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_benefit():
    """Fixture para benefício de exemplo."""
    return Benefit(
        id="benefit-123",
        tenant_id="knn",
        partner_id="partner-123",
        title="Desconto de 20% em pratos principais",
        description="Desconto especial para estudantes da KNN",
        discount_percentage=20.0,
        discount_value=None,
        category="alimentacao",
        configuration=BenefitConfiguration(
            requires_validation_code=True,
            max_uses_per_student=5,
            max_uses_per_month=2,
            valid_days_of_week=[1, 2, 3, 4, 5],
            valid_hours_start="11:00",
            valid_hours_end="22:00"
        ),
        limits=BenefitLimits(
            min_purchase_value=50.0,
            max_discount_value=100.0,
            applicable_products=["pratos principais", "combos"],
            excluded_products=["bebidas", "sobremesas"]
        ),
        terms_and_conditions="Válido apenas para estudantes com matrícula ativa",
        active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestPartnerEndpointsValidation:
    """Testes de validação para endpoints de parceiros."""

    @patch("src.api.student.firestore_client")
    def test_student_partners_endpoint_structure(self, mock_firestore, client, mock_student_user):
        """Testa se o endpoint de parceiros retorna dados na estrutura esperada pelo frontend."""
        # Mock dos dados do Firestore
        mock_partner_doc = MagicMock()
        mock_partner_doc.to_dict.return_value = {
            "id": "partner-123",
            "tenant_id": "knn",
            "trade_name": "Restaurante Teste",
            "legal_name": "Restaurante Teste LTDA",
            "cnpj": "12.345.678/0001-90",
            "category": "alimentacao",
            "description": "Restaurante especializado em comida brasileira",
            "address": {
                "street": "Rua das Flores, 123",
                "neighborhood": "Centro",
                "city": "São Paulo",
                "state": "SP",
                "zip_code": "01234-567",
                "country": "Brasil"
            },
            "contact_phone": "(11) 1234-5678",
            "contact_email": "contato@restauranteteste.com.br",
            "website": "https://restauranteteste.com.br",
            "social_networks": {
                "instagram": "@restauranteteste",
                "facebook": "restauranteteste",
                "twitter": "@restteste"
            },
            "logo_url": "https://example.com/logo.png",
            "banner_url": "https://example.com/banner.png",
            "active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        mock_firestore.collection.return_value.where.return_value.where.return_value.limit.return_value.stream.return_value = [mock_partner_doc]

        with patch("src.api.student.verify_token", return_value=mock_student_user):
            response = client.get("/v1/student/partners")

        assert response.status_code == 200
        data = response.json()

        # Validar estrutura da resposta
        assert "partners" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

        # Validar estrutura do parceiro
        if data["partners"]:
            partner = data["partners"][0]
            required_fields = [
                "id", "trade_name", "category", "description",
                "address", "contact_phone", "contact_email",
                "logo_url", "active"
            ]
            for field in required_fields:
                assert field in partner, f"Campo {field} não encontrado na resposta"

    @patch("src.api.employee.firestore_client")
    def test_employee_partners_endpoint_structure(self, mock_firestore, client, mock_employee_user):
        """Testa se o endpoint de parceiros para funcionários retorna dados corretos."""
        # Mock similar ao teste anterior
        mock_partner_doc = MagicMock()
        mock_partner_doc.to_dict.return_value = {
            "id": "partner-123",
            "tenant_id": "knn",
            "trade_name": "Restaurante Teste",
            "category": "alimentacao",
            "active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        mock_firestore.collection.return_value.where.return_value.where.return_value.limit.return_value.stream.return_value = [mock_partner_doc]

        with patch("src.api.employee.verify_token", return_value=mock_employee_user):
            response = client.get("/v1/employee/partners")

        assert response.status_code == 200
        data = response.json()

        # Validar que a resposta tem a mesma estrutura para consistência
        assert "partners" in data
        assert "total" in data


class TestFavoritesEndpointsValidation:
    """Testes de validação para endpoints de favoritos."""

    @patch("src.api.student.firestore_client")
    def test_student_favorites_get_structure(self, mock_firestore, client, mock_student_user):
        """Testa se o endpoint de favoritos do estudante retorna estrutura correta."""
        # Mock dos dados de favoritos
        mock_favorites_doc = MagicMock()
        mock_favorites_doc.exists = True
        mock_favorites_doc.to_dict.return_value = {
            "student_id": "STD_A3C1M7L7_S4",
            "tenant_id": "knn",
            "partner_ids": ["partner-123", "partner-456"],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_favorites_doc

        with patch("src.api.student.verify_token", return_value=mock_student_user):
            response = client.get("/v1/student/me/favorites")

        assert response.status_code == 200
        data = response.json()

        # Validar estrutura esperada pelo frontend
        required_fields = ["student_id", "partner_ids", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data, f"Campo {field} não encontrado na resposta de favoritos"

    @patch("src.api.student.firestore_client")
    def test_student_add_favorite_validation(self, mock_firestore, client, mock_student_user):
        """Testa validação ao adicionar favorito."""
        # Mock para verificar se o parceiro existe
        mock_partner_doc = MagicMock()
        mock_partner_doc.exists = True
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_partner_doc

        # Mock para favoritos existentes
        mock_favorites_doc = MagicMock()
        mock_favorites_doc.exists = True
        mock_favorites_doc.to_dict.return_value = {
            "student_id": "STD_A3C1M7L7_S4",
            "partner_ids": []
        }
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_favorites_doc

        favorite_request = {
            "partner_id": "partner-123"
        }

        with patch("src.api.student.verify_token", return_value=mock_student_user):
            response = client.post("/v1/student/me/favorites", json=favorite_request)

        # Deve aceitar requisição válida
        assert response.status_code in [200, 201]

    def test_favorite_request_model_validation(self):
        """Testa validação do modelo FavoriteRequest."""
        # Teste com dados válidos
        valid_request = FavoriteRequest(partner_id="partner-123")
        assert valid_request.partner_id == "partner-123"

        # Teste com dados inválidos
        with pytest.raises(ValueError):
            FavoriteRequest(partner_id="")  # ID vazio deve falhar


class TestBenefitsEndpointsValidation:
    """Testes de validação para endpoints de benefícios."""

    @patch("src.api.student.firestore_client")
    def test_partner_benefits_structure(self, mock_firestore, client, mock_student_user):
        """Testa se o endpoint de benefícios retorna estrutura esperada."""
        # Mock dos dados de benefícios
        mock_benefit_doc = MagicMock()
        mock_benefit_doc.to_dict.return_value = {
            "id": "benefit-123",
            "tenant_id": "knn",
            "partner_id": "partner-123",
            "title": "Desconto de 20%",
            "description": "Desconto especial",
            "discount_percentage": 20.0,
            "category": "alimentacao",
            "configuration": {
                "requires_validation_code": True,
                "max_uses_per_student": 5
            },
            "active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        mock_firestore.collection.return_value.where.return_value.where.return_value.stream.return_value = [mock_benefit_doc]

        with patch("src.api.student.verify_token", return_value=mock_student_user):
            response = client.get("/v1/student/partners/partner-123/benefits")

        assert response.status_code == 200
        data = response.json()

        # Validar estrutura dos benefícios
        assert "benefits" in data
        if data["benefits"]:
            benefit = data["benefits"][0]
            required_fields = [
                "id", "title", "description", "discount_percentage",
                "category", "configuration", "active"
            ]
            for field in required_fields:
                assert field in benefit, f"Campo {field} não encontrado no benefício"


class TestDataConsistencyValidation:
    """Testes para validar consistência de dados entre frontend e backend."""

    def test_partner_model_consistency(self, sample_partner):
        """Testa se o modelo Partner está consistente com os tipos TypeScript."""
        # Serializar para JSON (simula resposta da API)
        partner_dict = sample_partner.model_dump()

        # Campos obrigatórios que o frontend espera
        frontend_required_fields = [
            "id", "trade_name", "category", "description",
            "address", "contact_phone", "contact_email",
            "logo_url", "active"
        ]

        for field in frontend_required_fields:
            assert field in partner_dict, f"Campo {field} ausente no modelo Partner"

        # Validar estrutura do endereço
        address = partner_dict["address"]
        address_fields = ["street", "city", "state", "zip_code"]
        for field in address_fields:
            assert field in address, f"Campo {field} ausente no endereço"

    def test_benefit_model_consistency(self, sample_benefit):
        """Testa se o modelo Benefit está consistente com os tipos TypeScript."""
        benefit_dict = sample_benefit.model_dump()

        # Campos obrigatórios que o frontend espera
        frontend_required_fields = [
            "id", "partner_id", "title", "description",
            "discount_percentage", "category", "configuration", "active"
        ]

        for field in frontend_required_fields:
            assert field in benefit_dict, f"Campo {field} ausente no modelo Benefit"

        # Validar estrutura da configuração
        config = benefit_dict["configuration"]
        config_fields = ["requires_validation_code", "max_uses_per_student"]
        for field in config_fields:
            assert field in config, f"Campo {field} ausente na configuração"

    def test_favorites_model_consistency(self):
        """Testa se os modelos de favoritos estão consistentes."""
        # Teste StudentFavorites
        student_favorites = StudentFavorites(
            student_id="STD_A3C1M7L7_S4",
            tenant_id="knn",
            partner_ids=["partner-123", "partner-456"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        favorites_dict = student_favorites.model_dump()
        required_fields = ["student_id", "partner_ids", "created_at", "updated_at"]

        for field in required_fields:
            assert field in favorites_dict, f"Campo {field} ausente em StudentFavorites"

        # Teste EmployeeFavorites
        employee_favorites = EmployeeFavorites(
            employee_id="EMP_A0A0O007_AP",
            tenant_id="knn",
            partner_ids=["partner-123"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        emp_favorites_dict = employee_favorites.model_dump()
        emp_required_fields = ["employee_id", "partner_ids", "created_at", "updated_at"]

        for field in emp_required_fields:
            assert field in emp_favorites_dict, f"Campo {field} ausente em EmployeeFavorites"


class TestErrorHandlingValidation:
    """Testes para validar tratamento de erros."""

    @patch("src.api.student.firestore_client")
    def test_invalid_partner_id_error(self, mock_firestore, client, mock_student_user):
        """Testa tratamento de erro para ID de parceiro inválido."""
        # Mock para parceiro não encontrado
        mock_partner_doc = MagicMock()
        mock_partner_doc.exists = False
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_partner_doc

        with patch("src.api.student.verify_token", return_value=mock_student_user):
            response = client.get("/v1/student/partners/invalid-id/benefits")

        # Deve retornar erro apropriado
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data

    def test_invalid_favorite_request_validation(self, client, mock_student_user):
        """Testa validação de requisição inválida para favoritos."""
        invalid_request = {
            "partner_id": ""  # ID vazio
        }

        with patch("src.api.student.verify_token", return_value=mock_student_user):
            response = client.post("/v1/student/me/favorites", json=invalid_request)

        # Deve retornar erro de validação
        assert response.status_code == 422


class TestPaginationValidation:
    """Testes para validar paginação."""

    @patch("src.api.student.firestore_client")
    def test_partners_pagination_structure(self, mock_firestore, client, mock_student_user):
        """Testa se a paginação retorna estrutura correta."""
        # Mock de dados paginados
        mock_firestore.collection.return_value.where.return_value.where.return_value.limit.return_value.stream.return_value = []

        with patch("src.api.student.verify_token", return_value=mock_student_user):
            response = client.get("/v1/student/partners?page=1&per_page=10")

        assert response.status_code == 200
        data = response.json()

        # Validar estrutura de paginação
        pagination_fields = ["total", "page", "per_page", "partners"]
        for field in pagination_fields:
            assert field in data, f"Campo de paginação {field} não encontrado"

        # Validar tipos
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["per_page"], int)
        assert isinstance(data["partners"], list)
