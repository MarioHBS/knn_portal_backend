#!/usr/bin/env python3
"""
Teste Rápido de Endpoints Student - Portal KNN

Este script permite testar endpoints de estudante individualmente ou em conjunto,
utilizando um JWT token com renovação automática quando expirar.

Uso:
    python quick_student_test.py --all                    # Testa todos os endpoints
    python quick_student_test.py --endpoint partners      # Testa endpoint específico
    python quick_student_test.py --list                   # Lista endpoints disponíveis
    python quick_student_test.py --favorites              # Testa apenas endpoints de favoritos

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

# Adicionar o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from scripts.testing.e2e.base_auth_test import (  # noqa: E402
    BACKEND_BASE_URL,
    TEST_USERS,
    BaseAuthenticationTester,
)

# Configurações
JWT_TOKEN_FALLBACK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlc3R1ZGFudGUudGVzdGVAam91cm5leWNsdWIuY29tLmJyIiwicm9sZSI6InN0dWRlbnQiLCJ0ZW5hbnQiOiJrbm4tZGV2LXRlbmFudCIsImV4cCI6MTc1OTE1MDE3MiwiaWF0IjoxNzU5MTQ4MzcyLCJpc3MiOiJrbm4tcG9ydGFsLWxvY2FsIiwiYXVkIjoia25uLXBvcnRhbCIsIm5hbWUiOiJFc3R1ZGFudGUgZGUgVGVzdGUiLCJlbnRpdHlfaWQiOiJTVFVfRTBTMFQwNjlfQ0MifQ.example_token_hash"

# Arquivo de cache do token
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), "student_token_cache.json")

# Diretório para relatórios
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

# Mapeamento de endpoints disponíveis para estudantes
ENDPOINTS = {
    "partners": {
        "url": "/student/partners",
        "method": "GET",
        "description": "Lista de parceiros disponíveis",
        "category": "partners",
        "params": {"limit": 10, "offset": 0},
    },
    "partners_filtered": {
        "url": "/student/partners",
        "method": "GET",
        "description": "Lista de parceiros filtrados por categoria",
        "category": "partners",
        "params": {"cat": "alimentacao", "limit": 5},
    },
    "benefits": {
        "url": "/student/benefits",
        "method": "GET",
        "description": "Lista de benefícios disponíveis",
        "category": "benefits",
        "params": {"limit": 10, "offset": 0},
    },
    "benefits_filtered": {
        "url": "/student/benefits",
        "method": "GET",
        "description": "Lista de benefícios filtrados por categoria",
        "category": "benefits",
        "params": {"cat": "alimentacao", "limit": 5},
    },
    "partner_details": {
        "url": "/student/partners/{partner_id}",
        "method": "GET",
        "description": "Detalhes de um parceiro específico",
        "category": "partners",
        "url_params": {"partner_id": "PTN_A7E6314_EDU"},
    },
    "student_favorites": {
        "url": "/student/fav",
        "method": "GET",
        "description": "Lista de parceiros favoritos",
        "category": "favorites",
    },
    "add_favorite": {
        "url": "/student/fav",
        "method": "POST",
        "description": "Adicionar parceiro aos favoritos",
        "category": "favorites",
        "data": {"partner_id": "PTN_T4L5678_TEC"},
    },
    "remove_favorite": {
        "url": "/student/fav/{partner_id}",
        "method": "DELETE",
        "description": "Remover parceiro dos favoritos",
        "category": "favorites",
        "url_params": {"partner_id": "PTN_T4L5678_TEC"},
    },
    "create_validation_code": {
        "url": "/student/validation-codes",
        "method": "POST",
        "description": "Gerar código de validação para parceiro",
        "category": "validation",
        "data": {"partner_id": "PTN_T4L5678_TEC"},
    },
    "users_me": {
        "url": "/users/me",
        "method": "GET",
        "description": "Informações do usuário atual",
        "category": "profile",
    },
}


class QuickStudentTester:
    """Classe para testes rápidos de endpoints de estudante com renovação automática de JWT."""

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

            # Usa credenciais de estudante para renovar o token
            student_credentials = TEST_USERS["estudante_teste"]

            # Autentica no Firebase
            firebase_success, firebase_token = self.auth_tester.authenticate_firebase(
                student_credentials["email"], student_credentials["password"]
            )

            if not firebase_success or not firebase_token:
                self.print_colored("❌ Falha na autenticação Firebase", "red")
                return False

            # Faz login no backend
            backend_success, jwt_token = self.auth_tester.login_backend(
                firebase_token, student_credentials.get("role")
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
            except Exception:
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
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "white": "\033[0m",
            "cyan": "\033[96m",
            "magenta": "\033[95m",
        }

        color_code = colors.get(color, colors["white"])
        reset_code = "\033[0m"
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
        # Debug: Mostrar corpo da requisição quando aplicável
        if method in ["POST", "PUT", "DELETE"] and data is not None:
            try:
                self.print_colored(
                    f"   📦 Payload: {json.dumps(data, ensure_ascii=False)}",
                    "magenta",
                )
            except Exception:
                self.print_colored(f"   📦 Payload (raw): {data}", "magenta")

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
                                    endpoint_key == "student_history"
                                    and "items" in data_content
                                ):
                                    history_count = len(data_content["items"])
                                    result["history_count"] = history_count
                                    self.print_colored(
                                        f"   📊 Histórico de resgates: {history_count}",
                                        "cyan",
                                    )
                                elif endpoint_key == "student_favorites":
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
                # Tentar identificar se é 404 por recurso/dado não encontrado
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", error_data)
                    if isinstance(detail, dict):
                        msg = detail.get("msg") or detail.get("message") or str(detail)
                        code = detail.get("code")
                        if code:
                            self.print_colored(
                                f"   ⚠️  Recurso não encontrado: {msg} (code: {code})",
                                "yellow",
                            )
                        else:
                            self.print_colored(
                                f"   ⚠️  Recurso não encontrado: {msg}", "yellow"
                            )
                        result["error"] = msg
                        result["resource_not_found"] = True
                    else:
                        # Mensagem simples
                        self.print_colored(
                            f"   ⚠️  Recurso não encontrado: {detail}", "yellow"
                        )
                        result["error"] = str(detail)
                        result["resource_not_found"] = True
                except json.JSONDecodeError:
                    # Se não houver JSON, manter mensagem padrão
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

        self.print_header(f"TESTANDO {len(endpoint_keys)} ENDPOINTS DE ESTUDANTE")

        for i, endpoint_key in enumerate(endpoint_keys, 1):
            self.print_colored(f"\n[{i}/{len(endpoint_keys)}]", "cyan")
            result = self.test_endpoint(endpoint_key)
            results.append(result)

        return results

    def test_by_category(self, category: str) -> list[dict[str, Any]]:
        """
        Testa endpoints por categoria.

        Args:
            category: Categoria dos endpoints (partners, favorites, profile, validation)

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
                f"❌ Nenhum endpoint encontrado para categoria: {category}", "red"
            )
            return []

        self.print_colored(f"🎯 Testando categoria: {category.upper()}", "blue")
        return self.test_multiple_endpoints(category_endpoints)

    def list_endpoints(self) -> None:
        """Lista todos os endpoints disponíveis."""
        self.print_header("ENDPOINTS DISPONÍVEIS PARA ESTUDANTES")

        categories = {}
        for key, config in ENDPOINTS.items():
            category = config.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append((key, config))

        for category, endpoints in categories.items():
            self.print_colored(f"\n📂 {category.upper()}", "cyan")
            for key, config in endpoints:
                method_color = {
                    "GET": "green",
                    "POST": "blue",
                    "PUT": "yellow",
                    "DELETE": "red",
                }.get(config["method"], "white")

                self.print_colored(
                    f"  • {key:<25} [{config['method']}] {config['description']}",
                    method_color,
                )

    def print_summary(self, results: list[dict[str, Any]]) -> None:
        """
        Imprime resumo dos resultados dos testes.

        Args:
            results: Lista com resultados dos testes
        """
        if not results:
            return

        self.print_header("RESUMO DOS TESTES")

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        token_renewed = [r for r in results if r.get("token_renewed", False)]

        self.print_colored(f"✅ Sucessos: {len(successful)}", "green")
        self.print_colored(f"❌ Falhas: {len(failed)}", "red")
        self.print_colored(f"🔄 Tokens renovados: {len(token_renewed)}", "blue")

        if failed:
            self.print_colored("\n❌ ENDPOINTS COM FALHA:", "red")
            for result in failed:
                error_msg = result.get("error", "Erro desconhecido")
                self.print_colored(f"  • {result['endpoint_key']}: {error_msg}", "red")

        # Estatísticas por categoria
        categories = {}
        for result in results:
            endpoint_key = result["endpoint_key"]
            if endpoint_key in ENDPOINTS:
                category = ENDPOINTS[endpoint_key].get("category", "other")
                if category not in categories:
                    categories[category] = {"success": 0, "total": 0}
                categories[category]["total"] += 1
                if result["success"]:
                    categories[category]["success"] += 1

        if categories:
            self.print_colored("\n📊 ESTATÍSTICAS POR CATEGORIA:", "cyan")
            for category, stats in categories.items():
                success_rate = (stats["success"] / stats["total"]) * 100
                self.print_colored(
                    f"  • {category}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)",
                    "cyan",
                )

    def run_validation_flow(self) -> None:
        """Executa um fluxo completo de validação de código."""
        self.print_header("FLUXO COMPLETO DE VALIDAÇÃO")

        # 1. Listar parceiros
        self.print_colored("1️⃣ Listando parceiros disponíveis...", "blue")
        partners_result = self.test_endpoint("partners")

        if not partners_result.get("success"):
            self.print_colored("❌ Falha ao listar parceiros. Abortando fluxo.", "red")
            return

        # Extrair ID do primeiro parceiro da lista
        partner_id = None
        try:
            # A resposta da API é {"data": [...]}
            partners_list = partners_result.get("response_data", {}).get("data")

            if partners_list and isinstance(partners_list, list) and partners_list:
                # Filtrar parceiros com benefícios ativos
                active_partners = [
                    p for p in partners_list if p.get("has_active_benefits")
                ]

                if active_partners:
                    partner_id = active_partners[0].get("id")
                    self.print_colored(
                        f"✅ ID do parceiro com benefícios ativos extraído: {partner_id}",
                        "green",
                    )
                else:
                    self.print_colored(
                        "⚠️ Nenhum parceiro com benefícios ativos encontrado na lista.",
                        "yellow",
                    )
                    return
            else:
                self.print_colored("⚠️ Nenhum parceiro encontrado na lista.", "yellow")
                self.print_colored(
                    f"   🔍 Resposta recebida: {partners_result.get('response_data')}",
                    "yellow",
                )
                return

        except (AttributeError, IndexError, TypeError) as e:
            self.print_colored(f"❌ Erro ao extrair ID do parceiro: {e}", "red")
            return

        # Atualizar dinamicamente o ID do parceiro para os próximos testes
        if partner_id:
            ENDPOINTS["partner_details"]["url_params"]["partner_id"] = partner_id
            ENDPOINTS["create_validation_code"]["data"]["partner_id"] = partner_id
            self.print_colored(
                "🔧 Endpoints 'partner_details' e 'create_validation_code' atualizados com o novo ID.",
                "magenta",
            )

        # 2. Ver detalhes de um parceiro
        self.print_colored("2️⃣ Obtendo detalhes do parceiro...", "blue")
        partner_details_result = self.test_endpoint("partner_details")
        self.print_colored(
            f"🔍 Detalhes do parceiro: {partner_details_result}", "yellow"
        )

        # 3. Gerar código de validação
        self.print_colored("3️⃣ Gerando código de validação...", "blue")
        validation_result = self.test_endpoint("create_validation_code")

        if validation_result.get("success"):
            response_data = validation_result.get("response_data", {}).get("data", {})
            code = response_data.get("code")
            expires = response_data.get("expires")

            self.print_colored("✅ Código gerado com sucesso!", "green")
            self.print_colored(f"   🎫 Código: {code}", "cyan")
            self.print_colored(f"   ⏰ Expira em: {expires}", "cyan")

            # Simular que o código seria usado pelo parceiro
            self.print_colored("4️⃣ Código pronto para uso pelo parceiro!", "green")
        else:
            self.print_colored("❌ Falha ao gerar código de validação", "red")

        # 4. Verificar histórico
        self.print_colored("5️⃣ Verificando histórico de resgates...", "blue")
        self.test_endpoint("student_history")


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Teste rápido de endpoints de estudante do Portal KNN"
    )
    parser.add_argument("--all", action="store_true", help="Testa todos os endpoints")
    parser.add_argument("--endpoint", type=str, help="Testa um endpoint específico")
    parser.add_argument(
        "--category", type=str, help="Testa endpoints de uma categoria específica"
    )
    parser.add_argument(
        "--list", action="store_true", help="Lista todos os endpoints disponíveis"
    )
    parser.add_argument(
        "--flow", action="store_true", help="Executa fluxo completo de validação"
    )
    parser.add_argument(
        "--favorites", action="store_true", help="Testa apenas endpoints de favoritos"
    )
    parser.add_argument(
        "--partners", action="store_true", help="Testa apenas endpoints de parceiros"
    )
    parser.add_argument(
        "--profile", action="store_true", help="Testa apenas endpoints de perfil"
    )

    args = parser.parse_args()

    # Criar instância do testador
    tester = QuickStudentTester()

    # Processar argumentos
    if args.list:
        tester.list_endpoints()
        return

    if args.flow:
        tester.run_validation_flow()
        return

    results = []

    if args.all:
        results = tester.test_multiple_endpoints(list(ENDPOINTS.keys()))
    elif args.endpoint:
        if args.endpoint in ENDPOINTS:
            result = tester.test_endpoint(args.endpoint)
            results = [result]
        else:
            tester.print_colored(f"❌ Endpoint '{args.endpoint}' não encontrado", "red")
            tester.print_colored("Use --list para ver endpoints disponíveis", "yellow")
            return
    elif args.category:
        results = tester.test_by_category(args.category)
    elif args.favorites:
        results = tester.test_by_category("favorites")
    elif args.partners:
        results = tester.test_by_category("partners")
    elif args.profile:
        results = tester.test_by_category("profile")
    else:
        # Comportamento padrão: testar endpoints principais
        main_endpoints = [
            "users_me",
            "partners",
            "student_favorites",
            "student_history",
        ]
        results = tester.test_multiple_endpoints(main_endpoints)

    # Imprimir resumo
    if results:
        tester.print_summary(results)

    # Salvar resultados em arquivo JSON
    if results:
        # Criar diretório de relatórios se não existir
        os.makedirs(REPORTS_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(
            REPORTS_DIR, f"student_test_results_{timestamp}.json"
        )

        try:
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            tester.print_colored(f"📄 Resultados salvos em: {results_file}", "green")
        except Exception as e:
            tester.print_colored(f"⚠️ Erro ao salvar resultados: {e}", "yellow")


if __name__ == "__main__":
    main()
