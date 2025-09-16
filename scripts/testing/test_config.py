#!/usr/bin/env python3
"""
Configuração centralizada para testes do Portal de Benefícios KNN.

Este módulo contém todas as configurações necessárias para execução
dos testes automatizados dos endpoints da API.
"""

import os
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURAÇÕES BÁSICAS
# =============================================================================

# URLs base para diferentes ambientes
BASE_URLS = {
    "development": "http://localhost:8000/v1",
    "staging": "https://knn-portal-hml.cloudrun.app/v1",
    "production": "https://knn-portal.cloudrun.app/v1",
}

# Ambiente padrão
DEFAULT_ENVIRONMENT = "development"

# URL base atual (pode ser sobrescrita por variável de ambiente)
BASE_URL = os.getenv("TEST_BASE_URL", BASE_URLS[DEFAULT_ENVIRONMENT])

# Timeout para requisições HTTP (em segundos)
REQUEST_TIMEOUT = 30.0

# Configurações de retry
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # segundos

# =============================================================================
# TOKENS DE AUTENTICAÇÃO PARA TESTES
# =============================================================================

# Tokens JWT válidos para diferentes perfis (válidos até 2025-12-31)
TEST_TOKENS = {
    "student": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50LWlkIiwicm9sZSI6InN0dWRlbnQiLCJleHAiOjE3MTY5OTIwMDAsImlhdCI6MTcxNjkwNTYwMH0.8Uj7hl5vYGnEZQGR5QeQQOdTKB4ZXEfEiqxJxlE5Pjw",
    "employee": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZS1pZCIsInJvbGUiOiJlbXBsb3llZSIsImV4cCI6MTcxNjk5MjAwMCwiaWF0IjoxNzE2OTA1NjAwfQ.Kj8Hn5Fq5qSVBN5QjuoYd2KBjTIGJJoV9OQh-VzpNqJ",
    "partner": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJ0bmVyLWlkIiwicm9sZSI6InBhcnRuZXIiLCJleHAiOjE3MTY5OTIwMDAsImlhdCI6MTcxNjkwNTYwMH0.Hn5Fq5qSVBN5QjuoYd2KBjTIGJJoV9OQh-VzpNqJrSs",
    "admin": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbi1pZCIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcxNjk5MjAwMCwiaWF0IjoxNzE2OTA1NjAwfQ.jQyOq0-KnzH0vqBQwKsqzTBGzKqGLYVj9WdAZKbK5Hs",
}

# Headers padrão para requisições
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "KNN-Portal-Test-Suite/1.0",
}

# =============================================================================
# MAPEAMENTO DE ENDPOINTS POR PERFIL
# =============================================================================

# Endpoints para perfil Student
STUDENT_ENDPOINTS = {
    "list_partners": {
        "method": "GET",
        "path": "/student/partners",
        "description": "Lista parceiros disponíveis para estudantes",
        "params": ["cat", "ord", "limit", "offset"],
    },
    "get_partner_details": {
        "method": "GET",
        "path": "/student/partners/{id}",
        "description": "Obtém detalhes de um parceiro específico",
        "path_params": ["id"],
    },
    "create_validation_code": {
        "method": "POST",
        "path": "/student/validation-codes",
        "description": "Gera código de validação para resgate",
        "body_required": True,
    },
    "get_history": {
        "method": "GET",
        "path": "/student/me/history",
        "description": "Obtém histórico de resgates do estudante",
        "params": ["limit", "offset"],
    },
    "get_favorites": {
        "method": "GET",
        "path": "/student/me/fav",
        "description": "Lista parceiros favoritos do estudante",
    },
    "add_favorite": {
        "method": "POST",
        "path": "/student/me/fav",
        "description": "Adiciona parceiro aos favoritos",
        "body_required": True,
    },
    "remove_favorite": {
        "method": "DELETE",
        "path": "/student/me/fav/{pid}",
        "description": "Remove parceiro dos favoritos",
        "path_params": ["pid"],
    },
}

# Endpoints para perfil Employee
EMPLOYEE_ENDPOINTS = {
    "list_partners": {
        "method": "GET",
        "path": "/employee/partners",
        "description": "Lista parceiros disponíveis para funcionários",
        "params": ["cat", "ord", "limit", "offset"],
    },
    "get_partner_details": {
        "method": "GET",
        "path": "/employee/partners/{id}",
        "description": "Obtém detalhes de um parceiro específico",
        "path_params": ["id"],
    },
    "create_validation_code": {
        "method": "POST",
        "path": "/employee/validation-codes",
        "description": "Gera código de validação para resgate",
        "body_required": True,
    },
    "get_history": {
        "method": "GET",
        "path": "/employee/me/history",
        "description": "Obtém histórico de validações do funcionário",
    },
}

# Endpoints para perfil Admin
ADMIN_ENDPOINTS = {
    "list_partners": {
        "method": "GET",
        "path": "/admin/partners",
        "description": "Lista todos os parceiros (admin)",
        "params": ["cat", "ord", "limit", "offset"],
    },
    "get_partner_details": {
        "method": "GET",
        "path": "/admin/partners/{id}",
        "description": "Obtém detalhes de um parceiro (admin)",
        "path_params": ["id"],
    },
    "list_entities": {
        "method": "GET",
        "path": "/admin/{entity}",
        "description": "Lista entidades (students, partners, promotions)",
        "path_params": ["entity"],
        "params": ["limit", "offset"],
    },
    "create_entity": {
        "method": "POST",
        "path": "/admin/{entity}",
        "description": "Cria nova entidade",
        "path_params": ["entity"],
        "body_required": True,
    },
    "update_entity": {
        "method": "PUT",
        "path": "/admin/{entity}/{id}",
        "description": "Atualiza entidade existente",
        "path_params": ["entity", "id"],
        "body_required": True,
    },
    "delete_entity": {
        "method": "DELETE",
        "path": "/admin/{entity}/{id}",
        "description": "Remove entidade",
        "path_params": ["entity", "id"],
    },
    "get_metrics": {
        "method": "GET",
        "path": "/admin/metrics",
        "description": "Obtém métricas do sistema",
    },
    "send_notifications": {
        "method": "POST",
        "path": "/admin/notifications",
        "description": "Envia notificações",
        "body_required": True,
    },
}

# Endpoints para perfil Partner
PARTNER_ENDPOINTS = {
    "redeem_code": {
        "method": "POST",
        "path": "/partner/redeem",
        "description": "Resgatar código de validação",
        "body_required": True,
    },
    "list_promotions": {
        "method": "GET",
        "path": "/partner/promotions",
        "description": "Listar promoções do parceiro",
        "params": ["limit", "offset"],
    },
    "create_promotion": {
        "method": "POST",
        "path": "/partner/promotions",
        "description": "Criar nova promoção",
        "body_required": True,
    },
    "update_promotion": {
        "method": "PUT",
        "path": "/partner/promotions/{id}",
        "description": "Atualizar promoção existente",
        "path_params": ["id"],
        "body_required": True,
    },
    "delete_promotion": {
        "method": "DELETE",
        "path": "/partner/promotions/{id}",
        "description": "Deletar promoção",
        "path_params": ["id"],
    },
    "get_reports": {
        "method": "GET",
        "path": "/partner/reports",
        "description": "Obter relatórios do parceiro",
        "params": ["range"],
    },
}

# Endpoints utilitários (sem autenticação)
UTILS_ENDPOINTS = {
    "health_check": {
        "method": "GET",
        "path": "/health",
        "description": "Verifica status da API",
        "auth_required": False,
    },
    "get_courses": {
        "method": "GET",
        "path": "/utils/courses",
        "description": "Lista cursos disponíveis",
        "auth_required": False,
    },
}

# =============================================================================
# DADOS DE TESTE
# =============================================================================

# Dados para criação de entidades de teste
TEST_DATA = {
    "partner": {
        "trade_name": "Parceiro de Teste",
        "category": "Tecnologia",
        "address": "Rua de Teste, 123",
        "active": True,
        "cnpj": "12.345.678/0001-90",
    },
    "student": {
        "nome": "João Silva Santos",
        "email": "joao.teste@email.com",
        "telefone": "(11) 99999-9999",
        "cep": "01234-567",
        "curso": "KIDS 1",
        "data_nascimento": "2010-05-15",
        "nome_responsavel": "Maria Silva Santos",
    },
    "employee": {
        "nome": "Carlos Eduardo Silva",
        "email": "carlos.teste@escola.edu.br",
        "telefone": "(11) 88888-8888",
        "cep": "12345-678",
        "cargo": "Professor",
        "data_nascimento": "1985-03-20",
    },
    "promotion": {
        "title": "Promoção de Teste",
        "description": "Descrição da promoção de teste",
        "discount_percentage": 15.0,
        "audience": ["ENSINO_MEDIO", "GRADUACAO"],
        "valid_from": datetime.now().isoformat(),
        "valid_until": (datetime.now() + timedelta(days=30)).isoformat(),
    },
    "validation_code_request": {"partner_id": "test-partner-id"},
    "redeem_request": {"code": "TEST123", "cnpj": "12.345.678/0001-90"},
    "notification": {
        "target": "students",
        "filter": {},
        "message": "Mensagem de teste",
        "type": "both",
    },
}

# =============================================================================
# CONFIGURAÇÕES DE RELATÓRIOS
# =============================================================================

# Diretório para salvar relatórios
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")

# Formatos de relatório disponíveis
REPORT_FORMATS = ["json", "html", "txt"]

# Template HTML para relatórios
HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Testes - Portal KNN</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .summary { background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .test-group { margin: 20px 0; }
        .test-item { margin: 10px 0; padding: 10px; border-left: 4px solid #bdc3c7; }
        .test-pass { border-left-color: #27ae60; background: #d5f4e6; }
        .test-fail { border-left-color: #e74c3c; background: #fadbd8; }
        .test-skip { border-left-color: #f39c12; background: #fdeaa7; }
        .metrics { display: flex; justify-content: space-around; margin: 20px 0; }
        .metric { text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Relatório de Testes - Portal de Benefícios KNN</h1>
        <p>Gerado em: {timestamp}</p>
    </div>

    <div class="summary">
        <h2>Resumo Executivo</h2>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value" style="color: #27ae60;">{passed}</div>
                <div>Aprovados</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #e74c3c;">{failed}</div>
                <div>Falharam</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #f39c12;">{skipped}</div>
                <div>Ignorados</div>
            </div>
            <div class="metric">
                <div class="metric-value">{total}</div>
                <div>Total</div>
            </div>
        </div>
        <p><strong>Taxa de Sucesso:</strong> {success_rate:.1f}%</p>
        <p><strong>Tempo Total:</strong> {duration:.2f}s</p>
    </div>

    {test_results}
</body>
</html>
"""

# =============================================================================
# CONFIGURAÇÕES DE LOGGING
# =============================================================================

# Configurações de log
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "test_execution.log",
}

# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================


def get_auth_headers(role: str) -> dict[str, str]:
    """Retorna headers de autenticação para o perfil especificado."""
    headers = DEFAULT_HEADERS.copy()
    if role in TEST_TOKENS:
        headers["Authorization"] = f"Bearer {TEST_TOKENS[role]}"
    return headers


def get_endpoint_config(role: str, endpoint_name: str) -> dict | None:
    """Retorna configuração de um endpoint específico."""
    endpoint_maps = {
        "student": STUDENT_ENDPOINTS,
        "employee": EMPLOYEE_ENDPOINTS,
        "admin": ADMIN_ENDPOINTS,
        "partner": PARTNER_ENDPOINTS,
        "utils": UTILS_ENDPOINTS,
    }

    if role in endpoint_maps:
        return endpoint_maps[role].get(endpoint_name)
    return None


def get_all_endpoints() -> dict[str, dict]:
    """Retorna todos os endpoints organizados por perfil."""
    return {
        "student": STUDENT_ENDPOINTS,
        "employee": EMPLOYEE_ENDPOINTS,
        "admin": ADMIN_ENDPOINTS,
        "partner": PARTNER_ENDPOINTS,
        "utils": UTILS_ENDPOINTS,
    }


def build_url(path: str, **path_params) -> str:
    """Constrói URL completa substituindo parâmetros de path."""
    url = BASE_URL + path
    for param, value in path_params.items():
        url = url.replace(f"{{{param}}}", str(value))
    return url


# =============================================================================
# VALIDAÇÃO DE CONFIGURAÇÃO
# =============================================================================


def validate_config() -> bool:
    """Valida se todas as configurações estão corretas."""
    try:
        # Verificar se BASE_URL está definida
        if not BASE_URL:
            raise ValueError("BASE_URL não está definida")

        # Verificar se todos os tokens estão presentes
        required_roles = ["student", "employee", "admin", "partner"]
        for role in required_roles:
            if role not in TEST_TOKENS or not TEST_TOKENS[role]:
                raise ValueError(f"Token para perfil '{role}' não está definido")

        # Verificar se diretório de relatórios pode ser criado
        os.makedirs(REPORTS_DIR, exist_ok=True)

        return True

    except Exception as e:
        print(f"Erro na validação da configuração: {e}")
        return False


if __name__ == "__main__":
    # Validar configuração ao importar
    if validate_config():
        print("✅ Configuração validada com sucesso")
        print(f"📍 URL Base: {BASE_URL}")
        print(f"📁 Diretório de Relatórios: {REPORTS_DIR}")
    else:
        print("❌ Erro na validação da configuração")
        exit(1)
