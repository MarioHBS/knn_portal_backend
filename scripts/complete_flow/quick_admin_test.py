#!/usr/bin/env python3
"""
Teste Rápido de Endpoints Admin - Portal KNN

Este script permite testar endpoints administrativos individualmente ou em conjunto,
utilizando um JWT token com renovação automática quando expirar.

Uso:
    python quick_admin_test.py --all                    # Testa todos os endpoints
    python quick_admin_test.py --endpoint users_me      # Testa endpoint específico
    python quick_admin_test.py --list                   # Lista endpoints disponíveis
    python quick_admin_test.py --benefits               # Testa apenas endpoints de benefícios

Autor: Sistema de Testes KNN
Data: 2025-09-29
"""

import argparse
import json
import os
import sys
from contextlib import suppress
from datetime import datetime
from typing import Any

import requests
from base_auth_test import BACKEND_BASE_URL, TEST_USERS, BaseAuthenticationTester

# Configurações
JWT_TOKEN_FALLBACK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmZWxpcGVkZWZvbGl2ZUBnbWFpbC5jb20iLCJyb2xlIjoiYWRtaW4iLCJ0ZW5hbnQiOiJrbm4tZGV2LXRlbmFudCIsImV4cCI6MTc1OTE1MDE3MiwiaWF0IjoxNzU5MTQ4MzcyLCJpc3MiOiJrbm4tcG9ydGFsLWxvY2FsIiwiYXVkIjoia25uLXBvcnRhbCIsIm5hbWUiOiJGZWxpcGUgRmVycmVpcmEgZGUgT2xpdmVpcmEiLCJlbnRpdHlfaWQiOiJFTVBfRjBGME8wNjlfQ0MifQ.tLYMSPwaNi9Rs65SpYZpX_YcuLh9LJSKm8Eqq-dg4Hc"

# Arquivo de cache do token
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), "token_cache.json")

# Diretório para relatórios
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

# Mapeamento de endpoints disponíveis
ENDPOINTS = {
    "users_me": {
        "url": "/users/me",
        "method": "GET",
        "description": "Informações do usuário atual",
        "category": "user",
    },
    "admin_partners": {
        "url": "/admin/partners",
        "method": "GET",
        "description": "Lista de parceiros (admin)",
        "category": "admin",
    },
    "admin_students": {
        "url": "/admin/students",
        "method": "GET",
        "description": "Lista de estudantes (admin)",
        "category": "admin",
    },
    "admin_employees": {
        "url": "/admin/employees",
        "method": "GET",
        "description": "Lista de funcionários (admin)",
        "category": "admin",
    },
    "admin_benefits": {
        "url": "/admin/benefits",
        "method": "GET",
        "description": "Lista de benefícios (admin)",
        "category": "benefits",
    },
    "get_specific_benefit": {
        "url": "/admin/benefits/{partner_id}/{benefit_id}",
        "method": "GET",
        "description": "Obter detalhes de um benefício específico",
        "category": "benefits",
        "url_params": {"partner_id": "PTN_T4L5678_TEC", "benefit_id": "BNF_4A9B21_DC"},
    },
    "admin_metrics": {
        "url": "/admin/metrics",
        "method": "GET",
        "description": "Métricas administrativas",
        "category": "admin",
    },
    "admin_metrics_counters": {
        "url": "/admin/metrics/counters",
        "method": "GET",
        "description": "Contadores agregados (admin)",
        "category": "admin",
    },
    "admin_notifications": {
        "url": "/admin/notifications",
        "method": "POST",
        "description": "Envio de notificações (admin)",
        "category": "admin",
        "data": {
            "target": "students",
            "type": "push",
            "title": "Teste de Notificação",
            "message": "Esta é uma notificação de teste do admin",
        },
    },
    "create_employee": {
        "url": "/admin/employees",
        "method": "POST",
        "description": "Criar novo funcionário",
        "category": "admin",
        "data": {
            "name": "Funcionário Teste Rápido",
            "email": "funcionario.teste.rapido@example.com",
            # Campos opcionais usados para geração de ID padronizado
            # O endpoint /admin/employees irá gerar o ID via IDGenerators.gerar_id_funcionario
            # com base em name, cargo/role, cep e telefone.
            "cargo": "Analista",
            "cep": "88000000",
            "telefone": "+55 (48) 99999-0000",
        },
    },
    "delete_employee": {
        "url": "/admin/employees/{id}",
        "method": "DELETE",
        "description": "Deletar funcionário por ID",
        "category": "admin",
        "url_params": {"id": "EMP_F0T0R000_XX"},
    },
    "create_partner": {
        "url": "/admin/partners",
        "method": "POST",
        "description": "Criar novo parceiro",
        "category": "admin",
        "data": {
            "name": "Parceiro Teste Rápido",
            "category": "education",
            "active": True,
        },
    },
    "create_benefit": {
        "url": "/admin/benefits",
        "method": "POST",
        "description": "Criar novo benefício",
        "category": "benefits",
        "data": {
            "partner_id": "PTN_T4L5678_TEC",
            "title": "Benefício de Teste Rápido",
            "description": "Descrição do benefício de teste criado pelo quick test",
            "value": 15,
            "category": "desconto",
            "type": "percentage",
            "valid_from": "2025-01-01T00:00:00Z",
            "valid_to": "2025-12-31T23:59:59Z",
            "active": True,
            "audience": ["employee"],
        },
    },
    "update_benefit": {
        "url": "/admin/benefits/{partner_id}/{benefit_id}",
        "method": "PUT",
        "description": "Atualizar benefício",
        "category": "benefits",
        "data": {
            "title": "Benefício de Teste Rápido Atualizado",
            "description": "Descrição atualizada do benefício de teste",
            "value": 20,
            "category": "desconto",
            "type": "discount",
            "valid_from": "2025-01-01T00:00:00Z",
            "valid_to": "2025-12-31T23:59:59Z",
            "active": True,
            "audience": ["employee", "student"],
        },
        "url_params": {"partner_id": "PTN_T4L5678_TEC", "benefit_id": "BNF_272D2F_DC"},
    },
    "delete_benefit": {
        "url": "/admin/benefits/{partner_id}/{benefit_id}",
        "method": "DELETE",
        "description": "Deletar benefício",
        "category": "benefits",
        "data": {
            "partner_id": "PTN_T4L5678_TEC",
            "benefit_id": "BNF_D80F96_DC",
        },
        "url_params": {"partner_id": "PTN_T4L5678_TEC", "benefit_id": "BNF_D80F96_DC"},
    },
}


class QuickAdminTester:
    """Classe para testes rápidos de endpoints administrativos com renovação automática de JWT."""

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

            # Usa credenciais de admin para renovar o token
            admin_credentials = TEST_USERS[
                "admin_teste"
            ]  # Corrigido: usar "admin_teste"

            # Autentica no Firebase
            firebase_success, firebase_token = self.auth_tester.authenticate_firebase(
                admin_credentials["email"], admin_credentials["password"]
            )

            if not firebase_success or not firebase_token:
                self.print_colored("❌ Falha na autenticação Firebase", "red")
                return False

            # Faz login no backend
            backend_success, jwt_token = self.auth_tester.login_backend(
                firebase_token, admin_credentials.get("role")
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
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "white": "\033[0m",
            "cyan": "\033[96m",
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
        self.print_colored(f"   🔧 URL final: {url}", "magenta")

        try:
            # Fluxo especial para criação de funcionário com verificação de contadores antes/depois
            if endpoint_key == "create_employee":
                counters_url = f"{BACKEND_BASE_URL}/admin/metrics/counters"
                headers = {
                    "Authorization": f"Bearer {self.jwt_token}",
                    "Content-Type": "application/json",
                }

                # Obter contadores antes
                counters_before = None
                try:
                    cb_resp = self.session.get(
                        counters_url, headers=headers, timeout=20
                    )
                    if cb_resp.status_code in [200, 201]:
                        counters_before = cb_resp.json()
                        self.print_colored(
                            "   📊 Counters BEFORE obtidos com sucesso", "cyan"
                        )
                        # Logs adicionais com timestamps formatados
                        with suppress(Exception):
                            _data = (
                                counters_before.get("data", {})
                                if isinstance(counters_before, dict)
                                else {}
                            )
                            _agg_lu = self._format_timestamp(_data.get("last_updated"))
                            _emp = _data.get("employees", {})
                            _emp_lu = (
                                self._format_timestamp(_emp.get("last_updated"))
                                if isinstance(_emp, dict)
                                else None
                            )
                            if _agg_lu:
                                self.print_colored(
                                    f"   • last_updated (agregado BEFORE): {_agg_lu}",
                                    "white",
                                )
                            if _emp_lu:
                                self.print_colored(
                                    f"   • employees.last_updated BEFORE: {_emp_lu}",
                                    "white",
                                )
                    elif cb_resp.status_code == 401:
                        return {
                            "endpoint_key": endpoint_key,
                            "endpoint_url": endpoint_config["url"],
                            "method": method,
                            "description": endpoint_config["description"],
                            "status_code": cb_resp.status_code,
                            "success": False,
                            "timestamp": datetime.now().isoformat(),
                            "token_expired": True,
                            "error": "Token inválido ou expirado (counters BEFORE)",
                        }
                    else:
                        self.print_colored(
                            f"   ⚠️  Falha ao obter counters BEFORE: {cb_resp.status_code}",
                            "yellow",
                        )
                except requests.exceptions.RequestException as e:
                    self.print_colored(
                        f"   ⚠️  Erro ao obter counters BEFORE: {e}", "yellow"
                    )

                # Executar criação de funcionário
                create_resp = self.session.post(
                    url, json=data, headers=headers, timeout=30
                )
                result = {
                    "endpoint_key": endpoint_key,
                    "endpoint_url": endpoint_config["url"],
                    "method": method,
                    "description": endpoint_config["description"],
                    "status_code": create_resp.status_code,
                    "success": create_resp.status_code in [200, 201],
                    "timestamp": datetime.now().isoformat(),
                    "token_expired": False,
                }

                if create_resp.status_code == 401:
                    result["token_expired"] = True
                    result["error"] = "Token inválido ou expirado"
                    try:
                        result["response_data"] = create_resp.json()
                    except:
                        result["response_text"] = create_resp.text[:200]
                    return result

                # Obter contadores depois
                counters_after = None
                try:
                    ca_resp = self.session.get(
                        counters_url, headers=headers, timeout=20
                    )
                    if ca_resp.status_code in [200, 201]:
                        counters_after = ca_resp.json()
                        self.print_colored(
                            "   📊 Counters AFTER obtidos com sucesso", "cyan"
                        )
                        # Logs adicionais com timestamps formatados
                        with suppress(Exception):
                            _data = (
                                counters_after.get("data", {})
                                if isinstance(counters_after, dict)
                                else {}
                            )
                            _agg_lu = self._format_timestamp(_data.get("last_updated"))
                            _emp = _data.get("employees", {})
                            _emp_lu = (
                                self._format_timestamp(_emp.get("last_updated"))
                                if isinstance(_emp, dict)
                                else None
                            )
                            if _agg_lu:
                                self.print_colored(
                                    f"   • last_updated (agregado AFTER): {_agg_lu}",
                                    "white",
                                )
                            if _emp_lu:
                                self.print_colored(
                                    f"   • employees.last_updated AFTER: {_emp_lu}",
                                    "white",
                                )
                    else:
                        self.print_colored(
                            f"   ⚠️  Falha ao obter counters AFTER: {ca_resp.status_code}",
                            "yellow",
                        )
                except requests.exceptions.RequestException as e:
                    self.print_colored(
                        f"   ⚠️  Erro ao obter counters AFTER: {e}", "yellow"
                    )

                # Anexar dados da resposta de criação
                try:
                    resp_json = create_resp.json()
                    result["response_data"] = resp_json
                except json.JSONDecodeError:
                    result["response_text"] = create_resp.text[:200]

                # Adicionar counters before/after ao resultado
                if counters_before:
                    result["counters_before"] = counters_before
                if counters_after:
                    result["counters_after"] = counters_after

                # Se possível, calcular delta de employees
                try:
                    before_emp = (
                        counters_before.get("data", {})
                        .get("employees", {})
                        .get("total")
                        if isinstance(counters_before, dict)
                        else None
                    )
                    after_emp = (
                        counters_after.get("data", {}).get("employees", {}).get("total")
                        if isinstance(counters_after, dict)
                        else None
                    )
                    if before_emp is not None and after_emp is not None:
                        delta = after_emp - before_emp
                        result["employees_delta"] = delta
                        self.print_colored(
                            f"   📈 Employees delta: {delta} (before={before_emp}, after={after_emp})",
                            "cyan",
                        )
                except Exception as e:
                    self.print_colored(
                        f"   ⚠️  Não foi possível calcular delta: {e}", "yellow"
                    )

                # Retornar resultado consolidado
                return result

            # Fluxo especial para deleção de funcionário com verificação de contadores antes/depois
            if endpoint_key == "delete_employee":
                counters_url = f"{BACKEND_BASE_URL}/admin/metrics/counters"
                headers = {
                    "Authorization": f"Bearer {self.jwt_token}",
                    "Content-Type": "application/json",
                }

                # Obter contadores antes
                counters_before = None
                try:
                    cb_resp = self.session.get(
                        counters_url, headers=headers, timeout=20
                    )
                    if cb_resp.status_code in [200, 201]:
                        counters_before = cb_resp.json()
                        self.print_colored(
                            "   📊 Counters BEFORE obtidos com sucesso", "cyan"
                        )
                        # Logs adicionais com timestamps formatados
                        with suppress(Exception):
                            _data = (
                                counters_before.get("data", {})
                                if isinstance(counters_before, dict)
                                else {}
                            )
                            _agg_lu = self._format_timestamp(_data.get("last_updated"))
                            _emp = _data.get("employees", {})
                            _emp_lu = (
                                self._format_timestamp(_emp.get("last_updated"))
                                if isinstance(_emp, dict)
                                else None
                            )
                            if _agg_lu:
                                self.print_colored(
                                    f"   • last_updated (agregado BEFORE): {_agg_lu}",
                                    "white",
                                )
                            if _emp_lu:
                                self.print_colored(
                                    f"   • employees.last_updated BEFORE: {_emp_lu}",
                                    "white",
                                )
                    elif cb_resp.status_code == 401:
                        return {
                            "endpoint_key": endpoint_key,
                            "endpoint_url": endpoint_config["url"],
                            "method": method,
                            "description": endpoint_config["description"],
                            "status_code": cb_resp.status_code,
                            "success": False,
                            "timestamp": datetime.now().isoformat(),
                            "token_expired": True,
                            "error": "Token inválido ou expirado (counters BEFORE)",
                        }
                    else:
                        self.print_colored(
                            f"   ⚠️  Falha ao obter counters BEFORE: {cb_resp.status_code}",
                            "yellow",
                        )
                except requests.exceptions.RequestException as e:
                    self.print_colored(
                        f"   ⚠️  Erro ao obter counters BEFORE: {e}", "yellow"
                    )

                # Executar deleção de funcionário
                delete_resp = self.session.delete(url, headers=headers, timeout=30)
                result = {
                    "endpoint_key": endpoint_key,
                    "endpoint_url": endpoint_config["url"],
                    "method": method,
                    "description": endpoint_config["description"],
                    "status_code": delete_resp.status_code,
                    "success": delete_resp.status_code in [200, 201],
                    "timestamp": datetime.now().isoformat(),
                    "token_expired": False,
                }

                if delete_resp.status_code == 401:
                    result["token_expired"] = True
                    result["error"] = "Token inválido ou expirado"
                    try:
                        result["response_data"] = delete_resp.json()
                    except:
                        result["response_text"] = delete_resp.text[:200]
                    return result

                # Obter contadores depois
                counters_after = None
                try:
                    ca_resp = self.session.get(
                        counters_url, headers=headers, timeout=20
                    )
                    if ca_resp.status_code in [200, 201]:
                        counters_after = ca_resp.json()
                        self.print_colored(
                            "   📊 Counters AFTER obtidos com sucesso", "cyan"
                        )
                        # Logs adicionais com timestamps formatados
                        with suppress(Exception):
                            _data = (
                                counters_after.get("data", {})
                                if isinstance(counters_after, dict)
                                else {}
                            )
                            _agg_lu = self._format_timestamp(_data.get("last_updated"))
                            _emp = _data.get("employees", {})
                            _emp_lu = (
                                self._format_timestamp(_emp.get("last_updated"))
                                if isinstance(_emp, dict)
                                else None
                            )
                            if _agg_lu:
                                self.print_colored(
                                    f"   • last_updated (agregado AFTER): {_agg_lu}",
                                    "white",
                                )
                            if _emp_lu:
                                self.print_colored(
                                    f"   • employees.last_updated AFTER: {_emp_lu}",
                                    "white",
                                )
                    else:
                        self.print_colored(
                            f"   ⚠️  Falha ao obter counters AFTER: {ca_resp.status_code}",
                            "yellow",
                        )
                except requests.exceptions.RequestException as e:
                    self.print_colored(
                        f"   ⚠️  Erro ao obter counters AFTER: {e}", "yellow"
                    )

                # Adicionar counters before/after ao resultado
                if counters_before:
                    result["counters_before"] = counters_before
                if counters_after:
                    result["counters_after"] = counters_after

                # Se possível, calcular delta de employees
                try:
                    before_emp = (
                        counters_before.get("data", {})
                        .get("employees", {})
                        .get("total")
                        if isinstance(counters_before, dict)
                        else None
                    )
                    after_emp = (
                        counters_after.get("data", {}).get("employees", {}).get("total")
                        if isinstance(counters_after, dict)
                        else None
                    )
                    if before_emp is not None and after_emp is not None:
                        delta = after_emp - before_emp
                        result["employees_delta"] = delta
                        self.print_colored(
                            f"   📉 Employees delta: {delta} (before={before_emp}, after={after_emp})",
                            "cyan",
                        )
                except Exception as e:
                    self.print_colored(
                        f"   ⚠️  Não foi possível calcular delta: {e}", "yellow"
                    )

                # Retornar resultado consolidado
                return result

            # Fluxo especial para exibir counters normalizados
            if endpoint_key == "admin_metrics_counters":
                resp = self.session.get(url, headers=headers, timeout=20)
                result = {
                    "endpoint_key": endpoint_key,
                    "endpoint_url": endpoint_config["url"],
                    "method": method,
                    "description": endpoint_config["description"],
                    "status_code": resp.status_code,
                    "success": resp.status_code in [200, 201],
                    "timestamp": datetime.now().isoformat(),
                    "token_expired": False,
                }

                if resp.status_code == 401:
                    result["token_expired"] = True
                    result["error"] = "Token inválido ou expirado"
                    try:
                        result["response_data"] = resp.json()
                    except Exception:
                        result["response_text"] = resp.text[:200]
                    return result

                # Parse da resposta e normalização
                try:
                    resp_json = resp.json()
                    result["response_data"] = resp_json
                except json.JSONDecodeError:
                    result["response_text"] = resp.text[:500]
                    return result

                normalized = self._normalize_counters_response(result["response_data"])
                result["normalized_counters"] = normalized

                # Log amigável dos counters
                self.print_colored("   ✅ Contadores normalizados:", "green")
                # Última atualização agregada
                agg_lu = normalized.get("last_updated")
                agg_lu_fmt = self._format_timestamp(agg_lu)
                if agg_lu_fmt:
                    self.print_colored(
                        f"   • last_updated (agregado): {agg_lu_fmt}", "white"
                    )

                for entity in ["students", "employees", "partners", "benefits"]:
                    ent = normalized.get(entity, {})
                    total = ent.get("total")
                    lu = ent.get("last_updated")
                    lu_fmt = self._format_timestamp(lu)
                    self.print_colored(
                        f"   • {entity}: total={total} | last_updated={lu_fmt}",
                        "cyan",
                    )

                return result

            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = self.session.post(
                    url, json=data, headers=headers, timeout=30
                )
            elif method == "PUT":
                response = self.session.put(url, json=data, headers=headers, timeout=30)
            elif method == "DELETE":
                response = self.session.delete(
                    url, json=data, headers=headers, timeout=30
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
                response_text = response.text
                response_data = None
                with suppress(Exception):
                    response_data = response.json()
                if response_data is not None:
                    result["response_data"] = response_data

                    # Informações adicionais sobre a resposta
                    if isinstance(response_data, dict):
                        result["data_keys"] = list(response_data.keys())
                        if "data" in response_data:
                            data_content = response_data["data"]
                            if isinstance(data_content, list):
                                result["data_count"] = len(data_content)
                            elif isinstance(data_content, dict):
                                result["data_keys_nested"] = list(data_content.keys())

                                # Tratamento especial para endpoint admin_benefits
                                if (
                                    endpoint_key == "admin_benefits"
                                    and "items" in data_content
                                ):
                                    benefits_count = len(data_content["items"])
                                    total_benefits = data_content.get(
                                        "total", benefits_count
                                    )
                                    result["benefits_count"] = benefits_count
                                    result["total_benefits"] = total_benefits
                                    self.print_colored(
                                        f"   📊 Benefícios encontrados: {benefits_count} (total: {total_benefits})",
                                        "cyan",
                                    )
                else:
                    result["response_text"] = response_text[:200]  # Primeiros 200 chars

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
                error_data = None
                with suppress(Exception):
                    error_data = response.json()
                if error_data is not None:
                    self.print_colored(f"   🔍 Detalhes 401: {error_data}", "yellow")
                else:
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

                # Tentar obter detalhes do erro, sem estruturas complexas
                error_detail = None
                with suppress(Exception):
                    error_detail = response.json()
                if isinstance(error_detail, dict) and "detail" in error_detail:
                    result["error"] = error_detail["detail"]
                    print(f"   🔍 Detalhes do erro: {error_detail}")
                else:
                    result["error"] = response.text[:200]
                    print(f"   🔍 Resposta bruta: {response.text[:500]}")

        except Exception as e:
            # Captura erro não tratado na execução deste endpoint
            self.print_colored(
                f"   💥 Erro inesperado durante a requisição: {e}", "red"
            )
            return {
                "endpoint_key": endpoint_key,
                "endpoint_url": endpoint_config["url"],
                "method": method,
                "description": endpoint_config["description"],
                "status_code": -1,
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "token_expired": False,
                "error": str(e),
            }

        return result

    def _format_timestamp(self, ts: Any) -> str | None:
        """
        Formata timestamps para o padrão "yyyy-MM-dd HH:mm:ss".

        Aceita:
        - ISO 8601 com sufixo 'Z' (UTC)
        - ISO 8601 com offset (+00:00)
        - epoch (segundos) como int/float
        - strings já formatadas retornam como estão se parsing falhar
        """
        if ts is None:
            return None
        try:
            # Epoch em segundos
            if isinstance(ts, (int, float)):
                dt = datetime.utcfromtimestamp(ts)
                return dt.strftime("%Y-%m-%d %H:%M:%S")

            s = str(ts).strip()
            # Converter 'Z' para offset compatível com fromisoformat
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            # Fallback: retorna string original
            try:
                return str(ts)
            except Exception:
                return None

    def _normalize_counters_response(self, resp_json: dict[str, Any]) -> dict[str, Any]:
        """
        Normaliza o payload do endpoint /admin/metrics/counters para um formato simples:

        {
          last_updated: <agregado>,
          students: { total, last_updated },
          employees: { total, last_updated },
          partners: { total, last_updated },
          benefits: { total, last_updated }
        }
        """
        try:
            data = resp_json.get("data", resp_json)
            normalized: dict[str, Any] = {}

            # last_updated agregado (se existir)
            normalized["last_updated"] = data.get("last_updated")

            def _extract(ent: dict[str, Any]) -> dict[str, Any]:
                total = ent.get("total")
                if total is None:
                    # fallback para estrutura antiga
                    total = ent.get("totals", {}).get("quantity")
                return {
                    "total": total,
                    "last_updated": ent.get("last_updated"),
                }

            for entity in ["students", "employees", "partners", "benefits"]:
                normalized[entity] = _extract(data.get(entity, {}))

            return normalized
        except Exception as e:
            # Retorna um formato de erro simples; erros de rede não devem ocorrer aqui
            self.print_colored(f"   ⚠️ Falha ao normalizar counters: {e}", "yellow")
            return {"error": "failed_to_normalize"}

    def test_multiple_endpoints(self, endpoint_keys: list[str]) -> list[dict[str, Any]]:
        """
        Testa múltiplos endpoints.

        Args:
            endpoint_keys: Lista de chaves dos endpoints

        Returns:
            Lista com resultados dos testes
        """
        results = []

        self.print_header(f"TESTANDO {len(endpoint_keys)} ENDPOINTS")

        for i, endpoint_key in enumerate(endpoint_keys, 1):
            self.print_colored(f"\n[{i}/{len(endpoint_keys)}]", "cyan")
            result = self.test_endpoint(endpoint_key)
            results.append(result)

        return results

    def test_by_category(self, category: str) -> list[dict[str, Any]]:
        """
        Testa endpoints por categoria.

        Args:
            category: Categoria dos endpoints (admin, benefits, user)

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
        self.print_header("ENDPOINTS DISPONÍVEIS")

        categories = {}
        for key, config in ENDPOINTS.items():
            category = config.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append((key, config))

        for category, endpoints in categories.items():
            self.print_colored(f"\n📁 {category.upper()}:", "cyan")
            for key, config in endpoints:
                "green" if config["method"] == "GET" else "yellow"
                print(f"   {key:<20} ", end="")
                print(f"{config['method']:<6}", end="")
                print(f" {config['url']:<25}", end="")
                self.print_colored(f" - {config['description']}", "white")

    def save_results(
        self, results: list[dict[str, Any]], filename_suffix: str = ""
    ) -> str:
        """
        Salva os resultados em arquivo JSON.

        Args:
            results: Lista de resultados dos testes
            filename_suffix: Sufixo para o nome do arquivo

        Returns:
            Caminho do arquivo salvo
        """
        # Criar diretório de relatórios se não existir
        os.makedirs(REPORTS_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quick_admin_test_report_{timestamp}"
        if filename_suffix:
            filename += f"_{filename_suffix}"
        filename += ".json"

        filepath = os.path.join(REPORTS_DIR, filename)

        report_data = {
            "test_type": "quick_admin_test",
            "timestamp": datetime.now().isoformat(),
            "jwt_token": self.jwt_token,
            "total_tests": len(results),
            "successful_tests": sum(1 for r in results if r.get("success", False)),
            "failed_tests": sum(1 for r in results if not r.get("success", False)),
            "results": results,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            self.print_colored(f"📄 Relatório salvo: {filename}", "green")
            return filepath

        except Exception as e:
            self.print_colored(f"❌ Erro ao salvar relatório: {str(e)}", "red")
            return ""

    def print_summary(self, results: list[dict[str, Any]]) -> None:
        """
        Imprime resumo dos resultados.

        Args:
            results: Lista de resultados dos testes
        """
        if not results:
            return

        self.print_header("RESUMO DOS TESTES")

        total = len(results)
        successful = sum(1 for r in results if r.get("success", False))
        failed = total - successful

        self.print_colored(f"📊 Total de testes: {total}", "white")
        self.print_colored(f"✅ Sucessos: {successful}", "green")
        self.print_colored(f"❌ Falhas: {failed}", "red")
        self.print_colored(f"📈 Taxa de sucesso: {(successful/total*100):.1f}%", "cyan")

        if failed > 0:
            self.print_colored("\n🔍 FALHAS DETALHADAS:", "red")
            for result in results:
                if not result.get("success", False):
                    endpoint = result.get("endpoint_key", "unknown")
                    error = result.get("error", "Erro desconhecido")
                    self.print_colored(f"   • {endpoint}: {error}", "red")


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Teste rápido de endpoints administrativos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python quick_admin_test.py --all                    # Testa todos os endpoints
  python quick_admin_test.py --endpoint users_me      # Testa endpoint específico
  python quick_admin_test.py --list                   # Lista endpoints disponíveis
  python quick_admin_test.py --category benefits      # Testa categoria específica
  python quick_admin_test.py --endpoint users_me admin_partners  # Múltiplos endpoints
        """,
    )

    parser.add_argument(
        "--all", action="store_true", help="Testa todos os endpoints disponíveis"
    )

    parser.add_argument("--endpoint", nargs="+", help="Testa endpoint(s) específico(s)")

    parser.add_argument(
        "--category",
        choices=["admin", "benefits", "user"],
        help="Testa endpoints de uma categoria específica",
    )

    parser.add_argument(
        "--list", action="store_true", help="Lista todos os endpoints disponíveis"
    )

    parser.add_argument(
        "--save", action="store_true", help="Salva resultados em arquivo JSON"
    )

    args = parser.parse_args()

    tester = QuickAdminTester()

    # Verificar se nenhum argumento foi fornecido
    if not any([args.all, args.endpoint, args.category, args.list]):
        parser.print_help()
        return

    # Listar endpoints
    if args.list:
        tester.list_endpoints()
        return

    results = []

    try:
        # Testar todos os endpoints
        if args.all:
            endpoint_keys = list(ENDPOINTS.keys())
            results = tester.test_multiple_endpoints(endpoint_keys)

        # Testar endpoints específicos
        elif args.endpoint:
            results = tester.test_multiple_endpoints(args.endpoint)

        # Testar por categoria
        elif args.category:
            results = tester.test_by_category(args.category)

        # Imprimir resumo
        if results:
            tester.print_summary(results)

            # Salvar resultados se solicitado
            if args.save:
                suffix = ""
                if args.category:
                    suffix = args.category
                elif args.endpoint and len(args.endpoint) == 1:
                    suffix = args.endpoint[0]
                tester.save_results(results, suffix)

    except KeyboardInterrupt:
        tester.print_colored("\n⚠️ Teste interrompido pelo usuário", "yellow")
        sys.exit(1)
    except Exception as e:
        tester.print_colored(f"\n💥 Erro inesperado: {str(e)}", "red")
        sys.exit(1)


if __name__ == "__main__":
    main()
