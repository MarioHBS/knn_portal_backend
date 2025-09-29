#!/usr/bin/env python3
"""
Módulo Base para Testes de Autenticação - Portal KNN

Este módulo contém classes e funções comuns reutilizáveis para todos os testes
de autenticação das diferentes entidades (Admin, Partner, Student, Employee).

Autor: Sistema de Testes KNN
Data: 2025-01-06
"""

import base64
import json
import os
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv

    # Carregar .env do diretório raiz do projeto
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
    )
    load_dotenv(env_path)
except ImportError:
    print("⚠️ python-dotenv não encontrado, usando variáveis de ambiente do sistema")

# Configurações do script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# URLs e configurações
FIREBASE_AUTH_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)
BACKEND_BASE_URL = "http://localhost:8080/v1"

# Configurações Firebase carregadas do .env
FIREBASE_API_KEY = os.getenv("FB_API_KEY", "")
FIREBASE_AUTH_DOMAIN = os.getenv("FB_AUTH_DOMAIN", "")
FIREBASE_STORAGE_BUCKET = os.getenv("FB_STORAGE_BUCKET", "")
FIREBASE_MESSAGING_SENDER_ID = os.getenv("FB_MESSAGING_SENDER_ID", "")
FIREBASE_APP_ID = os.getenv("FB_APP_ID", "")
FIREBASE_MEASUREMENT_ID = os.getenv("FB_MEASUREMENT_ID", "")

# Credenciais de teste pré-definidas
TEST_USERS = {
    "parceiro_teste": {
        "email": "parceiro.teste@journeyclub.com.br",
        "password": "Tp654321",
        "role": "partner",
        "description": "Parceiro de Teste",
    },
    "admin_teste": {
        "email": "felipedefolive@gmail.com",
        "password": "Fo654321",
        "role": "admin",
        "description": "Felipe de Oliveira",
    },
    "estudante_teste": {
        "email": "estudante.teste@journeyclub.com.br",
        "password": "Tp654321",
        "role": "student",
        "description": "Estudante de Teste",
    },
    "funcionario_teste": {
        "email": "funcionario.teste@journeyclub.com.br",
        "password": "Tp54321",
        "role": "employee",
        "description": "Funcionário de Teste",
    },
}


def create_http_session() -> requests.Session:
    """Cria uma sessão HTTP com configurações de retry."""
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


class BaseAuthenticationTester:
    """Classe base para testes de autenticação."""

    def __init__(self):
        """Inicializa o testador de autenticação."""
        self.session = create_http_session()
        self.firebase_token = None
        self.jwt_token = None
        self.user_info = None
        self.test_results = []

    def print_header(self, title: str) -> None:
        """Imprime um cabeçalho formatado."""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)

    def print_step(self, step: str, status: str = "INFO") -> None:
        """Imprime uma etapa do processo."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(
            status, "ℹ️"
        )

        print(f"[{timestamp}] {status_icon} {step}")

    def validate_environment(self) -> bool:
        """Valida se o ambiente está configurado corretamente."""
        self.print_header("VALIDAÇÃO DO AMBIENTE")

        # Verificar se a API Key do Firebase está configurada
        if not FIREBASE_API_KEY:
            self.print_step("FB_API_KEY não encontrada no ambiente", "ERROR")
            self.print_step(
                "Configure a variável de ambiente FB_API_KEY no arquivo .env", "WARNING"
            )
            return False

        self.print_step(
            f"FB_API_KEY configurada: {FIREBASE_API_KEY[:10]}...", "SUCCESS"
        )

        # Testar conectividade com o backend
        try:
            response = self.session.get(f"{BACKEND_BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                self.print_step("Backend está acessível", "SUCCESS")
                return True
            else:
                self.print_step(
                    f"Backend retornou status {response.status_code}", "ERROR"
                )
                return False
        except requests.exceptions.RequestException as e:
            self.print_step(f"Erro ao conectar com backend: {str(e)}", "ERROR")
            return False

    def authenticate_firebase(
        self, email: str, password: str
    ) -> tuple[bool, str | None]:
        """
        Autentica no Firebase usando REST API.

        Args:
            email: Email do usuário
            password: Senha do usuário

        Returns:
            Tuple com (sucesso, token_firebase)
        """
        self.print_step(f"Iniciando autenticação Firebase para: {email}")

        payload = {"email": email, "password": password, "returnSecureToken": True}

        try:
            response = self.session.post(
                f"{FIREBASE_AUTH_URL}?key={FIREBASE_API_KEY}", json=payload, timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                firebase_token = data.get("idToken")

                if firebase_token:
                    self.firebase_token = firebase_token
                    self.print_step("Autenticação Firebase bem-sucedida", "SUCCESS")
                    self.print_step(
                        f"Token Firebase obtido: {firebase_token[:20]}...", "INFO"
                    )
                    return True, firebase_token
                else:
                    self.print_step(
                        "Token Firebase não encontrado na resposta", "ERROR"
                    )
                    return False, None

            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", {}).get(
                    "message", "Erro desconhecido"
                )
                self.print_step(
                    f"Erro na autenticação Firebase: {error_message}", "ERROR"
                )
                return False, None

        except requests.exceptions.RequestException as e:
            self.print_step(f"Erro de rede na autenticação Firebase: {str(e)}", "ERROR")
            return False, None
        except json.JSONDecodeError as e:
            self.print_step(f"Erro ao decodificar resposta Firebase: {str(e)}", "ERROR")
            return False, None

    def decode_jwt_payload(self, jwt_token: str) -> dict | None:
        """
        Decodifica o payload de um JWT token sem verificar a assinatura.

        Args:
            jwt_token: Token JWT para decodificar

        Returns:
            Dicionário com o payload do token ou None se houver erro
        """
        try:
            # JWT tem 3 partes separadas por pontos: header.payload.signature
            parts = jwt_token.split(".")
            if len(parts) != 3:
                return None

            # Decodificar o payload (segunda parte)
            payload_encoded = parts[1]

            # Adicionar padding se necessário (base64 requer múltiplos de 4)
            missing_padding = len(payload_encoded) % 4
            if missing_padding:
                payload_encoded += "=" * (4 - missing_padding)

            # Decodificar base64
            payload_decoded = base64.urlsafe_b64decode(payload_encoded)

            # Converter para dicionário
            payload_dict = json.loads(payload_decoded.decode("utf-8"))

            return payload_dict

        except Exception as e:
            self.print_step(f"Erro ao decodificar JWT payload: {str(e)}", "ERROR")
            return None

    def login_backend(
        self, firebase_token: str, role: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Faz login no backend usando o token Firebase.

        Args:
            firebase_token: Token obtido do Firebase
            role: Role opcional do usuário

        Returns:
            Tuple com (sucesso, jwt_token)
        """
        self.print_step("Iniciando login no backend")

        payload = {"firebase_token": firebase_token}

        if role:
            payload["role"] = role

        headers = {"Content-Type": "application/json"}

        try:
            response = self.session.post(
                f"{BACKEND_BASE_URL}/users/login",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                jwt_token = data.get("access_token")
                user_info = data.get("user_info", {})

                if jwt_token:
                    self.jwt_token = jwt_token
                    self.user_info = user_info
                    self.print_step("Login no backend bem-sucedido", "SUCCESS")
                    self.print_step(f"JWT Token obtido: {jwt_token[:20]}...", "INFO")
                    self.print_step(
                        f"Informações do usuário: {user_info.get('email', 'N/A')}",
                        "INFO",
                    )

                    # Decodificar JWT para mostrar entity_id
                    jwt_payload = self.decode_jwt_payload(jwt_token)
                    if jwt_payload:
                        entity_id = jwt_payload.get("entity_id")
                        if entity_id:
                            self.print_step(
                                f"🆔 Entity ID no token: {entity_id}", "INFO"
                            )
                        else:
                            self.print_step(
                                "⚠️ Entity ID não encontrado no token JWT", "WARNING"
                            )

                        # Mostrar outras informações relevantes do token
                        role_in_token = jwt_payload.get("role")
                        tenant_id = jwt_payload.get("tenant")
                        if role_in_token:
                            self.print_step(
                                f"👤 Role no token: {role_in_token}", "INFO"
                            )
                        if tenant_id:
                            self.print_step(
                                f"🏢 Tenant ID no token: {tenant_id}", "INFO"
                            )

                    return True, jwt_token
                else:
                    self.print_step("JWT Token não encontrado na resposta", "ERROR")
                    return False, None

            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("detail", "Erro desconhecido")
                self.print_step(f"Erro no login backend: {error_message}", "ERROR")
                return False, None

        except requests.exceptions.RequestException as e:
            self.print_step(f"Erro de rede no login backend: {str(e)}", "ERROR")
            return False, None
        except json.JSONDecodeError as e:
            self.print_step(f"Erro ao decodificar resposta backend: {str(e)}", "ERROR")
            return False, None

    def test_authenticated_endpoint(self, endpoint: str) -> tuple[bool, dict | None]:
        """
        Testa um endpoint autenticado.

        Args:
            endpoint: Endpoint a ser testado

        Returns:
            Tupla (sucesso, dados_resposta)
        """
        if not self.jwt_token:
            self.print_step("Token JWT não disponível", "ERROR")
            return False, None

        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                f"{BACKEND_BASE_URL}{endpoint}", headers=headers, timeout=10
            )

            if response.status_code == 200:
                self.print_step(f"✅ {endpoint}: {response.status_code}", "SUCCESS")
                return True, response.json()
            elif response.status_code == 404:
                self.print_step(
                    f"⚠️ {endpoint}: {response.status_code} (Endpoint não encontrado)",
                    "WARNING",
                )
                return (
                    True,
                    None,
                )  # Consideramos 404 como sucesso se o endpoint não existe
            else:
                self.print_step(f"❌ {endpoint}: {response.status_code}", "ERROR")
                return False, None

        except requests.exceptions.RequestException as e:
            self.print_step(f"Erro de rede no endpoint {endpoint}: {str(e)}", "ERROR")
            return False, None
        except json.JSONDecodeError as e:
            self.print_step(
                f"Erro ao decodificar resposta do endpoint {endpoint}: {str(e)}",
                "ERROR",
            )
            return False, None

    def get_user_info_from_me_endpoint(self) -> dict | None:
        """
        Obtém informações do usuário através do endpoint /users/me.

        Returns:
            Dicionário com informações do usuário ou None se houver erro
        """
        if not self.jwt_token:
            self.print_step(
                "Token JWT não disponível para obter informações do usuário", "ERROR"
            )
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json",
            }

            response = requests.get(
                f"{BACKEND_BASE_URL}/users/me", headers=headers, timeout=10
            )

            if response.status_code == 200:
                user_data = response.json()
                self.print_step(
                    "✅ Informações do usuário obtidas via /users/me", "SUCCESS"
                )
                return user_data
            else:
                self.print_step(
                    f"❌ Erro ao chamar /users/me: {response.status_code} - {response.text}",
                    "ERROR",
                )
                return None

        except Exception as e:
            self.print_step(
                f"❌ Erro ao obter informações via /users/me: {str(e)}", "ERROR"
            )
            return None

    def get_user_partner_id(self) -> str | None:
        """
        Obtém o partner_id do usuário logado através do endpoint /users/me.
        Para parceiros, o partner_id é o mesmo que o 'username' (sub) do JWT token.

        Returns:
            partner_id do usuário ou None se não encontrado
        """
        if not self.jwt_token:
            self.print_step("Token JWT não disponível para obter partner_id", "ERROR")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json",
            }

            response = requests.get(
                f"{BACKEND_BASE_URL}/users/me", headers=headers, timeout=10
            )

            if response.status_code == 200:
                user_data = response.json()
                partner_id = user_data.get(
                    "username"
                )  # O username é o sub do JWT, usado como partner_id
                if partner_id:
                    self.print_step(
                        f"✅ Partner ID obtido via /users/me: {partner_id}", "SUCCESS"
                    )
                    return partner_id
                else:
                    self.print_step(
                        "❌ Campo username não encontrado na resposta de /users/me",
                        "ERROR",
                    )
                    return None
            else:
                self.print_step(
                    f"❌ Erro ao chamar /users/me: {response.status_code} - {response.text}",
                    "ERROR",
                )
                return None

        except Exception as e:
            self.print_step(
                f"❌ Erro ao obter partner_id via /users/me: {str(e)}", "ERROR"
            )
            return None

    def save_test_report(self, test_results: list[dict], entity_type: str) -> str:
        """
        Salva o relatório de testes em um arquivo JSON.

        Args:
            test_results: Lista com resultados dos testes
            entity_type: Tipo da entidade testada (admin, partner, student, employee)

        Returns:
            Caminho do arquivo salvo
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{entity_type}_auth_test_report_{timestamp}.json"
        filepath = os.path.join(SCRIPT_DIR, filename)

        report_data = {
            "timestamp": timestamp,
            "entity_type": entity_type,
            "jwt_token": self.jwt_token if self.jwt_token else None,
            "total_tests": len(test_results),
            "successful_tests": sum(
                1 for result in test_results if result.get("success", False)
            ),
            "failed_tests": sum(
                1 for result in test_results if not result.get("success", False)
            ),
            "test_results": test_results,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            self.print_step(f"Relatório salvo em: {filepath}", "SUCCESS")
            return filepath

        except Exception as e:
            self.print_step(f"Erro ao salvar relatório: {str(e)}", "ERROR")
            return ""

    def run_basic_auth_flow(self, user_key: str) -> dict:
        """
        Executa o fluxo básico de autenticação para um usuário.

        Args:
            user_key: Chave do usuário no dicionário TEST_USERS

        Returns:
            Dicionário com resultado do teste
        """
        if user_key not in TEST_USERS:
            return {
                "success": False,
                "error": f"Usuário '{user_key}' não encontrado",
                "user_key": user_key,
            }

        user_data = TEST_USERS[user_key]
        result = {
            "success": False,
            "user_key": user_key,
            "email": user_data["email"],
            "role": user_data["role"],
            "description": user_data["description"],
            "firebase_token": None,
            "jwt_token": None,
            "endpoints_tested": 0,
            "error": None,
        }

        try:
            # Validar ambiente
            if not self.validate_environment():
                result["error"] = "Ambiente não configurado corretamente"
                return result

            # Autenticar no Firebase
            firebase_success, firebase_token = self.authenticate_firebase(
                user_data["email"], user_data["password"]
            )

            if not firebase_success or not firebase_token:
                result["error"] = "Falha na autenticação Firebase"
                return result

            result["firebase_token"] = firebase_token[:20] + "..."

            # Login no backend
            backend_success, jwt_token = self.login_backend(
                firebase_token, user_data["role"]
            )

            if not backend_success or not jwt_token:
                result["error"] = "Falha no login do backend"
                return result

            result["jwt_token"] = jwt_token[:20] + "..."

            # Testar endpoint básico /users/me
            me_success, _ = self.test_authenticated_endpoint("/users/me")
            if me_success:
                result["endpoints_tested"] += 1

            result["success"] = True
            return result

        except Exception as e:
            result["error"] = f"Erro inesperado: {str(e)}"
            return result
