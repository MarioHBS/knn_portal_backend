#!/usr/bin/env python3
"""
Teste Rápido de Endpoints Employee - Portal KNN

Este script permite testar endpoints de funcionário individualmente ou em conjunto,
utilizando um JWT token com renovação automática quando expirar.

Uso:
    python quick_employee_test.py --all                    # Testa todos os endpoints
    python quick_employee_test.py --endpoint partners      # Testa endpoint específico
    python quick_employee_test.py --list                   # Lista endpoints disponíveis
    python quick_employee_test.py --favorites              # Testa apenas endpoints de favoritos

Autor: Sistema de Testes KNN
Data: 2025-01-15
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any

import requests

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.complete_flow.base_auth_test import (
    BACKEND_BASE_URL,
    TEST_USERS,
    BaseAuthenticationTester,
)

# Configurações
JWT_TOKEN_FALLBACK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmdW5jaW9uYXJpby50ZXN0ZUBqb3VybmV5Y2x1Yi5jb20uYnIiLCJyb2xlIjoiZW1wbG95ZWUiLCJ0ZW5hbnQiOiJrbm4tZGV2LXRlbmFudCIsImV4cCI6MTc1OTE1MDE3MiwiaWF0IjoxNzU5MTQ4MzcyLCJpc3MiOiJrbm4tcG9ydGFsLWxvY2FsIiwiYXVkIjoia25uLXBvcnRhbCIsIm5hbWUiOiJGdW5jaW9uYXJpbyBkZSBUZXN0ZSIsImVudGl0eV9pZCI6IkVNUF8xMjM0NTZfQ0MifQ.example_token_hash"

# Arquivo de cache do token
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), "employee_token_cache.json")

# Diretório para relatórios
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

# Mapeamento de endpoints disponíveis para funcionários
ENDPOINTS = {
    "partners": {
        "url": "/employee/partners",
        "method": "GET",
        "description": "Lista de parceiros disponíveis",
        "category": "partners",
        "params": {"limit": 10, "offset": 0},
    },
    "partners_filtered": {
        "url": "/employee/partners",
        "method": "GET",
        "description": "Lista de parceiros filtrados por categoria",
        "category": "partners",
        "params": {"cat": "alimentacao", "limit": 5},
    },
    "partner_details": {
        "url": "/employee/partners/{partner_id}",
        "method": "GET",
        "description": "Detalhes de um parceiro específico",
        "category": "partners",
        "url_params": {"partner_id": "PTN_A7E6314_EDU"},
    },
    "create_validation_code": {
        "url": "/employee/validation-codes",
        "method": "POST",
        "description": "Gerar código de validação para parceiro",
        "category": "validation",
        "data": {"partner_id": "PTN_T4L5678_TEC"},
    },
    "employee_favorites": {
        "url": "/employee/me/fav",
        "method": "GET",
        "description": "Lista de parceiros favoritos",
        "category": "favorites",
    },
    "add_favorite": {
        "url": "/employee/me/fav",
        "method": "POST",
        "description": "Adicionar parceiro aos favoritos",
        "category": "favorites",
        "data": {"partner_id": "PTN_T4L5678_TEC"},
    },
    "remove_favorite": {
        "url": "/employee/me/fav/{partner_id}",
        "method": "DELETE",
        "description": "Remover parceiro dos favoritos",
        "category": "favorites",
        "url_params": {"partner_id": "PTN_T4L5678_TEC"},
    },
    "employee_history": {
        "url": "/employee/me/history",
        "method": "GET",
        "description": "Histórico de códigos de validação",
        "category": "history",
    },
    "users_me": {
        "url": "/users/me",
        "method": "GET",
        "description": "Informações do usuário atual",
        "category": "profile",
    },
}


class QuickEmployeeTester:
    """Classe para testes rápidos de endpoints de funcionário com renovação automática de JWT."""

    def __init__(self):
        """Inicializa o testador com configurações básicas."""
        self.session = requests.Session()
        self.jwt_token = self._load_token_from_cache()
        self.auth_tester = None  # Será inicializado quando necessário
        self.results = []

    def _load_token_from_cache(self) -> str:
        """
        Carrega o token JWT do arquivo de cache.

        Returns:
            Token JWT válido ou token fallback se não encontrado
        """
        try:
            if os.path.exists(TOKEN_CACHE_FILE):
                with open(TOKEN_CACHE_FILE, encoding="utf-8") as f:
                    cache_data = json.load(f)
                    token = cache_data.get("jwt_token")
                    if token:
                        self.print_colored("🔑 Token carregado do cache", "blue")
                        return token
        except Exception as e:
            self.print_colored(f"⚠️ Erro ao carregar token do cache: {e}", "yellow")

        self.print_colored("🔑 Usando token fallback", "blue")
        return JWT_TOKEN_FALLBACK

    def _save_token_to_cache(self, token: str) -> None:
        """
        Salva o token JWT no arquivo de cache.

        Args:
            token: Token JWT para salvar
        """
        try:
            cache_data = {
                "jwt_token": token,
                "updated_at": datetime.now().isoformat(),
                "source": "auto_renewal",
            }

            with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            self.print_colored("💾 Token salvo no cache", "green")
        except Exception as e:
            self.print_colored(f"❌ Erro ao salvar token no cache: {e}", "red")

    def _renew_jwt_token(self) -> bool:
        """
        Renova o token JWT usando o processo de autenticação completo.

        Returns:
            True se a renovação foi bem-sucedida, False caso contrário
        """
        try:
            self.print_colored("🔄 Renovando token JWT expirado...", "blue")

            # Inicializa o autenticador se necessário
            if not self.auth_tester:
                self.auth_tester = BaseAuthenticationTester()

            # Usa credenciais de funcionário para renovar o token
            employee_credentials = TEST_USERS["funcionario_teste"]

            # Autentica no Firebase
            firebase_success, firebase_token = self.auth_tester.authenticate_firebase(
                employee_credentials["email"], employee_credentials["password"]
            )

            if not firebase_success or not firebase_token:
                self.print_colored("❌ Falha na autenticação Firebase", "red")
                return False

            # Faz login no backend
            backend_success, jwt_token = self.auth_tester.login_backend(
                firebase_token, employee_credentials.get("role")
            )

            if not backend_success or not jwt_token:
                self.print_colored("❌ Falha no login do backend", "red")
                return False

            # Atualiza o token e salva no cache
            self.jwt_token = jwt_token
            self._save_token_to_cache(jwt_token)

            self.print_colored("✅ Token JWT renovado com sucesso!", "green")
            return True

        except Exception as e:
            self.print_colored(f"❌ Erro durante renovação do token: {e}", "red")
            return False

    def _is_token_expired_error(self, response: requests.Response) -> bool:
        """
        Verifica se o erro indica token expirado.

        Args:
            response: Resposta HTTP da requisição

        Returns:
            True se o erro indica token expirado
        """
        if response.status_code == 401:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("msg", "").lower()
                return "jwt" in error_msg and (
                    "inválido" in error_msg
                    or "expirado" in error_msg
                    or "expired" in error_msg
                )
            except:
                return True  # Assume token expirado para qualquer 401
        return False

    def print_colored(self, message: str, color: str = "white") -> None:
        """
        Imprime mensagem colorida no terminal.

        Args:
            message: Mensagem a ser impressa
            color: Cor da mensagem (green, red, yellow, blue, white)
        """
        colors = {
            "green": "[92m",
            "red": "[91m",
            "yellow": "[93m",
            "blue": "[94m",
            "white": "[0m",
            "cyan": "[96m",
            "magenta": "[95m",
        }

        color_code = colors.get(color, colors["white"])
        reset_code = "[0m"
        print(f"{color_code}{message}{reset_code}")

    def print_header(self, title: str) -> None:
        """Imprime cabeçalho formatado."""
        self.print_colored("=" * 60, "cyan")
        self.print_colored(f" {title} ", "cyan")
        self.print_colored("=" * 60, "cyan")

    def test_endpoint(self, endpoint_key: str) -> dict[str, Any]:
        """
        Testa um endpoint específico com renovação automática de JWT se necessário.

        Args:
            endpoint_key: Chave do endpoint no dicionário ENDPOINTS

        Returns:
            Dicionário com resultado do teste
        """
        if endpoint_key not in ENDPOINTS:
            return {
                "endpoint_key": endpoint_key,
                "success": False,
                "error": "Endpoint não encontrado",
                "timestamp": datetime.now().isoformat(),
            }

        # Primeira tentativa
        result = self._execute_endpoint_request(endpoint_key)

        # Se falhou por token expirado, tenta renovar e executar novamente
        if not result["success"] and result.get("token_expired", False):
            self.print_colored(
                "🔄 Token expirado detectado, tentando renovar...", "yellow"
            )

            if self._renew_jwt_token():
                self.print_colored("🔄 Executando novamente com novo token...", "blue")
                result = self._execute_endpoint_request(endpoint_key)
                result["token_renewed"] = True
            else:
                result["token_renewal_failed"] = True
                self.print_colored("❌ Falha na renovação do token", "red")

        return result

    def _execute_endpoint_request(self, endpoint_key: str) -> dict[str, Any]:
        """
        Executa a requisição para um endpoint específico.

        Args:
            endpoint_key: Chave do endpoint no dicionário ENDPOINTS

        Returns:
            Dicionário com resultado da requisição
        """
        endpoint_config = ENDPOINTS[endpoint_key]
        url = f"{BACKEND_BASE_URL}{endpoint_config['url']}"
        method = endpoint_config["method"]
        data = endpoint_config.get("data")
        params = endpoint_config.get("params")

        # Substituir parâmetros na URL se necessário
        if "url_params" in endpoint_config:
            for param_key, param_value in endpoint_config["url_params"].items():
                url = url.replace(f"{{{param_key}}}", str(param_value))

        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        self.print_colored(f"🔍 Testando: {endpoint_config['description']}", "blue")
        self.print_colored(f"   {method} {url}", "white")

        # Debug: Mostrar URL final construída
        if params:
            self.print_colored(f"   🔧 Parâmetros: {params}", "magenta")

        try:
            if method == "GET":
                response = self.session.get(
                    url, headers=headers, params=params, timeout=30
                )
            elif method == "POST":
                response = self.session.post(
                    url, json=data, headers=headers, params=params, timeout=30
                )
            elif method == "PUT":
                response = self.session.put(
                    url, json=data, headers=headers, params=params, timeout=30
                )
            elif method == "DELETE":
                response = self.session.delete(
                    url, json=data, headers=headers, params=params, timeout=30
                )
            else:
                return {
                    "endpoint_key": endpoint_key,
                    "success": False,
                    "error": f"Método HTTP não suportado: {method}",
                    "timestamp": datetime.now().isoformat(),
                }

            result = {
                "endpoint_key": endpoint_key,
                "endpoint_url": endpoint_config["url"],
                "method": method,
                "description": endpoint_config["description"],
                "status_code": response.status_code,
                "success": response.status_code in [200, 201],
                "timestamp": datetime.now().isoformat(),
                "token_expired": False,
            }

            if response.status_code in [200, 201]:
                self.print_colored(f"   ✅ Sucesso: {response.status_code}", "green")
                try:
                    response_data = response.json()
                    result["response_data"] = response_data

                    # Informações adicionais sobre a resposta
                    if isinstance(response_data, dict):
                        result["data_keys"] = list(response_data.keys())
                        if "data" in response_data:
                            data_content = response_data["data"]
                            if isinstance(data_content, list):
                                result["data_count"] = len(data_content)
                                self.print_colored(
                                    f"   📊 Itens encontrados: {len(data_content)}",
                                    "cyan",
                                )
                            elif isinstance(data_content, dict):
                                result["data_keys_nested"] = list(data_content.keys())

                                # Tratamento especial para diferentes endpoints
                                if (
                                    endpoint_key == "partners"
                                    and "items" in data_content
                                ):
                                    partners_count = len(data_content["items"])
                                    total_partners = data_content.get(
                                        "total", partners_count
                                    )
                                    result["partners_count"] = partners_count
                                    result["total_partners"] = total_partners
                                    self.print_colored(
                                        f"   📊 Parceiros encontrados: {partners_count} (total: {total_partners})",
                                        "cyan",
                                    )
                                elif (
                                    endpoint_key == "employee_history"
                                    and "items" in data_content
                                ):
                                    history_count = len(data_content["items"])
                                    result["history_count"] = history_count
                                    self.print_colored(
                                        f"   📊 Histórico de resgates: {history_count}",
                                        "cyan",
                                    )
                                elif endpoint_key == "employee_favorites":
                                    favorites_count = (
                                        len(data_content)
                                        if isinstance(data_content, list)
                                        else 0
                                    )
                                    result["favorites_count"] = favorites_count
                                    self.print_colored(
                                        f"   📊 Favoritos: {favorites_count}",
                                        "cyan",
                                    )
                                elif (
                                    endpoint_key == "create_validation_code"
                                    and "code" in data_content
                                ):
                                    self.print_colored(
                                        f"   🎫 Código gerado: {data_content['code']}",
                                        "cyan",
                                    )
                                    self.print_colored(
                                        f"   ⏰ Expira em: {data_content.get('expires', 'N/A')}",
                                        "cyan",
                                    )

                except json.JSONDecodeError:
                    result["response_text"] = response.text[:200]  # Primeiros 200 chars

            elif response.status_code == 404:
                self.print_colored(
                    f"   ⚠️  Endpoint não encontrado: {response.status_code}", "yellow"
                )
                result["error"] = "Endpoint não encontrado"
            elif response.status_code == 401:
                # Tratar especificamente erro 401 (Unauthorized)
                self.print_colored(
                    f"   🔐 Token inválido ou expirado: {response.status_code}",
                    "yellow",
                )
                result["token_expired"] = True
                result["error"] = "Token inválido ou expirado"
                try:
                    error_data = response.json()
                    self.print_colored(f"   🔍 Detalhes 401: {error_data}", "yellow")
                except json.JSONDecodeError:
                    self.print_colored(f"   🔍 Resposta 401: {response.text}", "yellow")
            else:
                # Verifica se é erro de token expirado
                if self._is_token_expired_error(response):
                    result["token_expired"] = True
                    self.print_colored(
                        f"   🔑 Token expirado: {response.status_code}", "yellow"
                    )
                else:
                    self.print_colored(f"   ❌ Erro: {response.status_code}", "red")

                try:
                    error_data = response.json()
                    result["error"] = error_data.get("detail", response.text)
                    # Imprimir detalhes do erro para debug
                    print(f"   🔍 Detalhes do erro: {error_data}")
                except json.JSONDecodeError:
                    result["error"] = response.text[:200]
                    print(f"   🔍 Resposta bruta: {response.text[:500]}")

            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de rede: {str(e)}"
            self.print_colored(f"   ❌ {error_msg}", "red")
            return {
                "endpoint_key": endpoint_key,
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "token_expired": False,
            }
        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            self.print_colored(f"   ❌ {error_msg}", "red")
            return {
                "endpoint_key": endpoint_key,
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "token_expired": False,
            }

    def test_multiple_endpoints(self, endpoint_keys: list[str]) -> list[dict[str, Any]]:
        """
        Testa múltiplos endpoints.

        Args:
            endpoint_keys: Lista de chaves dos endpoints

        Returns:
            Lista com resultados dos testes
        """
        results = []

        self.print_header(f"TESTANDO {len(endpoint_keys)} ENDPOINTS DE FUNCIONÁRIO")

        for i, endpoint_key in enumerate(endpoint_keys, 1):
            self.print_colored(f"\n[{i}/{len(endpoint_keys)}]", "cyan")
            result = self.test_endpoint(endpoint_key)
            results.append(result)

        return results

    def test_by_category(self, category: str) -> list[dict[str, Any]]:
        """
        Testa endpoints por categoria.

        Args:
            category: Categoria dos endpoints (partners, favorites, profile, validation, history)

        Returns:
            Lista com resultados dos testes
        """
        category_endpoints = [
            key
            for key, config in ENDPOINTS.items()
            if config.get("category") == category
        ]

        if not category_endpoints:
            self.print_colored(
                f"Nenhum endpoint encontrado para a categoria: {category}", "yellow"
            )
            return []

        return self.test_multiple_endpoints(category_endpoints)

    def save_report(self, results: list[dict[str, Any]], report_name: str) -> None:
        """
        Salva os resultados dos testes em um arquivo JSON.

        Args:
            results: Lista de resultados dos testes
            report_name: Nome do arquivo de relatório
        """
        if not os.path.exists(REPORTS_DIR):
            os.makedirs(REPORTS_DIR)

        report_path = os.path.join(REPORTS_DIR, report_name)

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.print_colored(f"\n📄 Relatório salvo em: {report_path}", "green")
        except Exception as e:
            self.print_colored(f"❌ Erro ao salvar relatório: {e}", "red")

    def list_endpoints(self) -> None:
        """Lista os endpoints disponíveis."""
        self.print_header("ENDPOINTS DE FUNCIONÁRIO DISPONÍVEIS")
        for key, config in ENDPOINTS.items():
            self.print_colored(f"- {key}:", "cyan")
            self.print_colored(f"  Descrição: {config['description']}", "white")
            self.print_colored(
                f"  Endpoint: {config['method']} {config['url']}", "white"
            )
            self.print_colored(f"  Categoria: {config['category']}", "white")


def main():
    """Função principal para executar os testes."""
    parser = argparse.ArgumentParser(
        description="Teste rápido de endpoints de funcionário do Portal KNN."
    )
    parser.add_argument("--all", action="store_true", help="Testar todos os endpoints.")
    parser.add_argument(
        "--endpoint", type=str, help="Testar um endpoint específico pelo nome."
    )
    parser.add_argument(
        "--category", type=str, help="Testar todos os endpoints de uma categoria."
    )
    parser.add_argument(
        "--list", action="store_true", help="Listar todos os endpoints disponíveis."
    )

    args = parser.parse_args()
    tester = QuickEmployeeTester()

    if args.list:
        tester.list_endpoints()
        return

    results = []
    report_name = (
        f"employee_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    if args.all:
        results = tester.test_multiple_endpoints(list(ENDPOINTS.keys()))
    elif args.endpoint:
        results = [tester.test_endpoint(args.endpoint)]
    elif args.category:
        results = tester.test_by_category(args.category)
    else:
        parser.print_help()
        return

    if results:
        tester.save_report(results, report_name)


if __name__ == "__main__":
    main()
