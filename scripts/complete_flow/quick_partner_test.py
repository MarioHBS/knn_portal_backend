"""
Teste Rápido de Endpoints de Parceiro - Portal KNN

Este script permite testar endpoints de parceiro individualmente ou em conjunto,
utilizando um JWT token com renovação automática quando expirar.

Uso:
    python quick_partner_test.py --all                    # Testa todos os endpoints
    python quick_partner_test.py --endpoint redeem        # Testa endpoint específico
    python quick_partner_test.py --list                   # Lista endpoints disponíveis

Autor: Sistema de Testes KNN
Data: 2025-09-30
"""

import argparse
import json
import os
import sys
from datetime import datetime

import jwt
import requests

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.complete_flow.base_auth_test import (
    BACKEND_BASE_URL,
    TEST_USERS,
    BaseAuthenticationTester,
)

# --- Configurações ---
JWT_TOKEN_FALLBACK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJjZWlyby50ZXN0ZUBqb3VybmV5Y2x1Yi5jb20uYnIiLCJyb2xlIjoicGFydG5lciIsInRlbmFudCI6Imtubi1kZXYtdGVuYW50IiwiZXhwIjoxNzU5MTUwMTcyLCJpYXQiOjE3NTkxNDgzNzIsImlzcyI6Imtubi1wb3J0YWwtbG9jYWwiLCJhdWQiOiJrbm4tcG9ydGFsIiwibmFtZSI6IlBhcmNlaXJvIGRlIFRlc3RlIiwiZW50aXR5X2lkIjoiUFROX0ExRTg5NThfQVVUIn0.example_token_hash"
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), "partner_token_cache.json")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "partner_reports")


# --- Endpoints ---
ENDPOINTS = {
    "redeem": {
        "method": "POST",
        "path": "/partner/redeem",
        "description": "Resgata um código de validação.",
        "data": {"code": "086207", "cnpj": "12.345.678/0001-90"},
    },
    "create_promotion": {
        "method": "POST",
        "path": "/partner/promotions",
        "description": "Cria uma nova promoção.",
        "data": {
            "title": "Desconto Especial de Teste via Script",
            "type": "discount",
            "valid_from": "2025-01-01T00:00:00",
            "valid_to": "2025-12-31T23:59:59",
            "active": True,
            "audience": ["student"],
            "discount_percentage": 15,
        },
    },
    "update_promotion": {
        "method": "PUT",
        "path": "/partner/promotions/{id}",
        "description": "Atualiza uma promoção existente.",
        "url_params": {"id": "PROMOTION_ID_HERE"},
        "data": {
            "title": "Desconto Atualizado de Teste via Script",
            "active": False,
            "audience": ["student", "employee"],
            "discount_percentage": 20,
        },
    },
    "delete_promotion": {
        "method": "DELETE",
        "path": "/partner/promotions/{id}",
        "description": "Remove uma promoção.",
        "url_params": {"id": "PROMOTION_ID_HERE"},
    },
    "get_reports": {
        "method": "GET",
        "path": "/partner/reports",
        "description": "Obtém o relatório de uso de promoções.",
        "params": {"range": "2025-09"},
    },
}


class QuickPartnerTester:
    """Classe para testar os endpoints de parceiros com renovação de token."""

    def __init__(self):
        """Inicializa o testador."""
        self.session = requests.Session()
        self.jwt_token = self._load_token_from_cache()
        self.partner_id = self._get_partner_id_from_token(self.jwt_token)
        self.auth_tester = None
        self.results = []
        self.last_promotion_id = None

    def _load_token_from_cache(self) -> str:
        """Carrega o token JWT do cache ou usa o fallback."""
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

    def _save_token_to_cache(self, token: str):
        """Salva o token JWT no cache."""
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

    def _get_partner_id_from_token(self, token: str) -> str | None:
        """Extrai o ID do parceiro do token JWT."""
        if not token:
            return None
        try:
            # Decodifica o payload sem verificar a assinatura para ler os dados
            payload = jwt.decode(token, options={"verify_signature": False})
            partner_id = payload.get("entity_id")
            if partner_id:
                self.print_colored(
                    f"👤 ID do Parceiro identificado: {partner_id}", "cyan"
                )
                return partner_id
        except jwt.PyJWTError as e:
            self.print_colored(
                f"⚠️ Erro ao decodificar token para obter ID: {e}", "yellow"
            )
        return None

    def _renew_jwt_token(self) -> bool:
        """Renova o token JWT usando o processo de autenticação."""
        try:
            self.print_colored("🔄 Renovando token JWT expirado...", "blue")
            if not self.auth_tester:
                self.auth_tester = BaseAuthenticationTester()

            partner_credentials = TEST_USERS["parceiro_teste"]
            firebase_success, firebase_token = self.auth_tester.authenticate_firebase(
                partner_credentials["email"], partner_credentials["password"]
            )
            if not firebase_success:
                self.print_colored("❌ Falha na autenticação Firebase", "red")
                return False

            backend_success, jwt_token = self.auth_tester.login_backend(
                firebase_token, partner_credentials.get("role")
            )
            if not backend_success:
                self.print_colored("❌ Falha no login do backend", "red")
                return False

            self.jwt_token = jwt_token
            self._save_token_to_cache(jwt_token)
            self.partner_id = self._get_partner_id_from_token(self.jwt_token)
            self.print_colored("✅ Token JWT renovado com sucesso!", "green")
            return True
        except Exception as e:
            self.print_colored(f"❌ Erro durante renovação do token: {e}", "red")
            return False

    def _is_token_expired_error(self, response: requests.Response) -> bool:
        """Verifica se a resposta indica um erro de token expirado ou inválido."""
        if response.status_code == 401:
            try:
                error_data = response.json()
                # Tenta extrair a mensagem de erro de diferentes formatos possíveis
                detail = error_data.get("detail")
                if isinstance(detail, dict):
                    error_msg = detail.get("error", {}).get("msg", "").lower()
                elif isinstance(detail, str):
                    error_msg = detail.lower()
                else:
                    error_msg = str(error_data).lower()

                # Condições para renovação
                is_jwt_error = "jwt" in error_msg
                is_expired = "expirado" in error_msg or "expired" in error_msg
                is_invalid_signature = "signature" in error_msg
                is_invalid = "inválido" in error_msg

                if is_jwt_error or is_expired or is_invalid_signature or is_invalid:
                    self.print_colored(
                        f"   ➡️  Detectado erro de token: {error_msg}", "yellow"
                    )
                    return True
            except json.JSONDecodeError:
                # Se a resposta não for JSON, mas for 401, é seguro assumir que o token é o problema
                self.print_colored(
                    "   ➡️  Detectado erro 401 sem JSON. Assumindo token inválido.",
                    "yellow",
                )
                return True
        return False

    def print_colored(self, message: str, color: str = "white"):
        """Imprime uma mensagem colorida no terminal."""
        colors = {
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "magenta": "\033[95m",
            "white": "\033[0m",
        }
        color_code = colors.get(color, colors["white"])
        reset_code = "\033[0m"
        print(f"{color_code}{message}{reset_code}")

    def print_header(self, title: str):
        """Imprime um cabeçalho formatado."""
        self.print_colored("=" * 60, "cyan")
        self.print_colored(f" {title} ", "cyan")
        self.print_colored("=" * 60, "cyan")

    def test_endpoint(self, endpoint_key: str, params: dict | None = None) -> dict:
        """Testa um endpoint, com renovação de token se necessário."""
        if endpoint_key not in ENDPOINTS:
            return {"success": False, "error": "Endpoint não encontrado"}

        result = self._execute_endpoint_request(endpoint_key, params)
        if not result["success"] and result.get("token_expired"):
            if self._renew_jwt_token():
                result = self._execute_endpoint_request(endpoint_key, params)
                result["token_renewed"] = True
            else:
                result["token_renewal_failed"] = True
        return result

    def _execute_endpoint_request(
        self, endpoint_key: str, params: dict | None = None
    ) -> dict:
        """Executa a requisição para o endpoint."""
        config = ENDPOINTS[endpoint_key]
        method = config["method"]
        url = f"{BACKEND_BASE_URL}{config['path']}"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        data = config.get("data", {}).copy()
        url_params = (params or {}).copy()

        # Lógica para substituir IDs dinamicamente
        if "update_promotion" in endpoint_key or "delete_promotion" in endpoint_key:
            if self.last_promotion_id:
                url_params["id"] = self.last_promotion_id
            else:
                self.print_colored(
                    f"⚠️ ID da promoção não encontrado para {endpoint_key}", "yellow"
                )
                return {"success": False, "error": "ID da promoção não encontrado"}

        # Substituir parâmetros na URL
        for key, value in url_params.items():
            url = url.replace(f"{{{key}}}", str(value))

        # Mesclar parâmetros de teste com dados padrão
        if params:
            data.update(params)

        # Validação específica para o endpoint de redeem
        if endpoint_key == "redeem":
            code = data.get("code")
            if not code or code == "VALIDATION_CODE_HERE":
                self.print_colored(
                    '⚠️ Código de validação não fornecido ou é um placeholder. Use --params \'{"code": "SEU_CODIGO"}\'.',
                    "yellow",
                )
                return {
                    "success": False,
                    "error": "Código de validação inválido ou não fornecido",
                }

        self.print_colored(f"🔍 Testando: {config['description']}", "blue")
        self.print_colored(f"   {method} {url}", "white")
        if data and method in ["POST", "PUT"]:
            self.print_colored(f"   Payload: {json.dumps(data, indent=2)}", "magenta")

        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                json=data if method in ["POST", "PUT"] else None,
                params=config.get("params") if method == "GET" else None,
            )
            result = {
                "endpoint_key": endpoint_key,
                "status_code": response.status_code,
                "success": response.ok,
                "timestamp": datetime.now().isoformat(),
            }
            if response.ok:
                self.print_colored(f"   ✅ Sucesso: {response.status_code}", "green")
                try:
                    response_data = response.json()
                    result["response_data"] = response_data
                    if endpoint_key == "create_promotion" and response_data.get(
                        "data", {}
                    ).get("id"):
                        self.last_promotion_id = response_data["data"]["id"]
                        self.print_colored(
                            f"   ✨ ID da promoção criada: {self.last_promotion_id}",
                            "cyan",
                        )
                except json.JSONDecodeError:
                    pass
            else:
                result["token_expired"] = self._is_token_expired_error(response)
                self.print_colored(f"   ❌ Erro: {response.status_code}", "red")
                try:
                    result["error_details"] = response.json()
                    self.print_colored(
                        f"      Detalhes: {result['error_details']}", "yellow"
                    )
                except json.JSONDecodeError:
                    result["error_details"] = response.text
            return result
        except requests.RequestException as e:
            self.print_colored(f"   ❌ Erro de rede: {e}", "red")
            return {"success": False, "error": str(e)}

    def test_all_endpoints(self):
        """Testa todos os endpoints em uma sequência lógica."""
        self.print_header("INICIANDO TESTE COMPLETO DE ENDPOINTS DE PARCEIRO")

        # 1. Criar promoção
        create_result = self.test_endpoint("create_promotion")
        self.results.append(create_result)

        # 2. Atualizar promoção
        if self.last_promotion_id:
            update_result = self.test_endpoint("update_promotion")
            self.results.append(update_result)

        # 3. Obter relatórios
        report_result = self.test_endpoint("get_reports")
        self.results.append(report_result)

        # 4. Deletar promoção
        if self.last_promotion_id:
            delete_result = self.test_endpoint("delete_promotion")
            self.results.append(delete_result)

        self.print_header("TESTE COMPLETO FINALIZADO")
        self.save_report(self.results, "partner_test_report.json")

    def save_report(self, data: list, filename: str):
        """Salva o relatório de teste em um arquivo JSON."""
        if not os.path.exists(REPORTS_DIR):
            os.makedirs(REPORTS_DIR)
        filepath = os.path.join(REPORTS_DIR, filename)
        report_content = {
            "partner_id": self.partner_id,
            "report_generated_at": datetime.now().isoformat(),
            "results": data,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_content, f, indent=2, ensure_ascii=False)
        self.print_colored(f"\n📄 Relatório salvo em: {filepath}", "cyan")


def main():
    """Função principal para executar os testes."""
    parser = argparse.ArgumentParser(
        description="Testador rápido para a API de Parceiros."
    )
    parser.add_argument("--endpoint", "-e", help="Nome do endpoint para testar.")
    parser.add_argument(
        "--params",
        "-p",
        type=json.loads,
        help='Parâmetros em formato JSON. Ex: \'{"code": "12345"}\'',
    )
    parser.add_argument(
        "--all", action="store_true", help="Testar todos os endpoints em sequência."
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="Listar todos os endpoints disponíveis.",
    )

    args = parser.parse_args()
    tester = QuickPartnerTester()

    if args.list:
        tester.print_header("ENDPOINTS DE PARCEIRO DISPONÍVEIS")
        for name, info in ENDPOINTS.items():
            print(f"- {name}: {info['description']}")
        return

    if args.all:
        tester.test_all_endpoints()
    elif args.endpoint:
        result = tester.test_endpoint(args.endpoint, args.params)
        tester.save_report([result], f"single_test_{args.endpoint}.json")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
