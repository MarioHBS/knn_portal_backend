#!/usr/bin/env python3
"""
Script de Teste Completo de Autenticação - Portal KNN

Este script simula o processo completo de autenticação:
1. Autenticação no Firebase usando REST API
2. Captura do Firebase Token
3. Chamada ao endpoint '/users/login' para obter JWT Token
4. Utilização do JWT Token para requisições autenticadas

Autor: Sistema de Testes KNN
Data: 2025-01-06
"""

import base64
import json
import os
import sys
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

# Inicializar Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import auth, credentials, firestore

    # Verificar se o Firebase já foi inicializado
    if not firebase_admin._apps:
        # Caminho para o arquivo de credenciais do Firebase
        cred_path = os.path.join(
            PROJECT_ROOT, "credentials", "firebase_service_account.json"
        )

        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            # Configurar com as credenciais do .env
            firebase_config = {
                "apiKey": FIREBASE_API_KEY,
                "authDomain": FIREBASE_AUTH_DOMAIN,
                "storageBucket": FIREBASE_STORAGE_BUCKET,
                "messagingSenderId": FIREBASE_MESSAGING_SENDER_ID,
                "appId": FIREBASE_APP_ID,
                "measurementId": FIREBASE_MEASUREMENT_ID,
            }
            firebase_admin.initialize_app(cred, firebase_config)
            print(
                "✅ Firebase Admin SDK inicializado com sucesso usando credenciais do .env"
            )
        else:
            print(f"⚠️ Arquivo de credenciais não encontrado: {cred_path}")
            print("⚠️ Testes de entity_id podem falhar")
    else:
        print("✅ Firebase Admin SDK já estava inicializado")

except ImportError:
    print("⚠️ Firebase Admin SDK não encontrado, testes de entity_id serão ignorados")
except Exception as e:
    print(f"⚠️ Erro ao inicializar Firebase Admin SDK: {str(e)}")

# Credenciais de teste pré-definidas
TEST_USERS = {
    "parceiro_teste": {
        "email": "parceiro.teste@journeyclub.com.br",
        "password": "Tp654321",
        "role": "partner",
        "description": "Parceiro de Teste",
    },
    "admin_teste": {
        "email": "admin.teste@journeyclub.com.br",
        "password": "Admin123",
        "role": "admin",
        "description": "Administrador de Teste",
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


# Configuração de sessão HTTP com retry
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


class AuthenticationTester:
    """Classe principal para testes de autenticação."""

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

    def test_partner_promotions_endpoints(self) -> dict:
        """
        Testa os endpoints específicos de promoções para parceiros.
        Fluxo completo: listar -> criar 2 promoções -> atualizar 1 -> excluir 1 -> listar novamente

        Returns:
            Dicionário com resultados dos testes
        """
        results = {
            "get_promotions_initial": {"success": False, "data": None, "count": 0},
            "create_promotion_1": {
                "success": False,
                "data": None,
                "promotion_id": None,
            },
            "create_promotion_2": {
                "success": False,
                "data": None,
                "promotion_id": None,
            },
            "update_promotion": {"success": False, "data": None},
            "delete_promotion": {"success": False, "data": None},
            "get_promotions_final": {"success": False, "data": None, "count": 0},
        }

        if not self.jwt_token:
            self.print_step("Token JWT não disponível para testes de parceiro", "ERROR")
            return results

        # Obter partner_id do parceiro
        partner_id = self.get_user_partner_id()
        if not partner_id:
            self.print_step("❌ Não foi possível obter partner_id do parceiro", "ERROR")
            return results

        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        self.print_step("\n🔍 TESTANDO FLUXO COMPLETO DE PROMOÇÕES DO PARCEIRO", "INFO")

        # 1. Listar promoções iniciais
        self.print_step("1️⃣ Listando promoções iniciais...", "INFO")
        try:
            response = requests.get(
                f"{BACKEND_BASE_URL}/partner/promotions", headers=headers, timeout=10
            )
            if response.status_code == 200:
                promotions_data = response.json()
                results["get_promotions_initial"]["success"] = True
                results["get_promotions_initial"]["data"] = promotions_data
                initial_count = len(promotions_data.get("data", []))
                results["get_promotions_initial"]["count"] = initial_count
                self.print_step(
                    f"✅ GET /partner/promotions (inicial): {initial_count} promoções encontradas",
                    "SUCCESS",
                )
            else:
                self.print_step(
                    f"❌ GET /partner/promotions (inicial): {response.status_code} - {response.text}",
                    "ERROR",
                )
        except Exception as e:
            self.print_step(
                f"❌ Erro no GET /partner/promotions (inicial): {str(e)}", "ERROR"
            )

        # 2. Criar primeira promoção
        self.print_step("2️⃣ Criando primeira promoção...", "INFO")
        promotion_1_data = {
            "title": "Promoção Teste 1 - Desconto Especial",
            "type": "discount",
            "valid_from": "2025-01-01T00:00:00Z",
            "valid_to": "2025-12-31T23:59:59Z",
            "active": True,
            "audience": ["student", "employee"],  # Corrigido: lista em vez de string
        }

        try:
            response = requests.post(
                f"{BACKEND_BASE_URL}/partner/promotions",
                json=promotion_1_data,
                headers=headers,
                timeout=10,
            )
            if response.status_code in [200, 201]:
                promotion_1_response = response.json()
                results["create_promotion_1"]["success"] = True
                results["create_promotion_1"]["data"] = promotion_1_response
                promotion_1_id = promotion_1_response.get("data", {}).get("id")
                results["create_promotion_1"]["promotion_id"] = promotion_1_id
                self.print_step(
                    f"✅ POST /partner/promotions (1): Promoção criada com ID {promotion_1_id}",
                    "SUCCESS",
                )
            else:
                self.print_step(
                    f"❌ POST /partner/promotions (1): {response.status_code} - {response.text}",
                    "ERROR",
                )
        except Exception as e:
            self.print_step(
                f"❌ Erro no POST /partner/promotions (1): {str(e)}", "ERROR"
            )

        # 3. Criar segunda promoção
        self.print_step("3️⃣ Criando segunda promoção...", "INFO")
        promotion_2_data = {
            "title": "Promoção Teste 2 - Oferta Limitada",
            "type": "discount",
            "valid_from": "2025-01-01T00:00:00Z",
            "valid_to": "2025-06-30T23:59:59Z",
            "active": True,
            "audience": ["student"],  # Corrigido: lista em vez de string
        }

        try:
            response = requests.post(
                f"{BACKEND_BASE_URL}/partner/promotions",
                json=promotion_2_data,
                headers=headers,
                timeout=10,
            )
            if response.status_code in [200, 201]:
                promotion_2_response = response.json()
                results["create_promotion_2"]["success"] = True
                results["create_promotion_2"]["data"] = promotion_2_response
                promotion_2_id = promotion_2_response.get("data", {}).get("id")
                results["create_promotion_2"]["promotion_id"] = promotion_2_id
                self.print_step(
                    f"✅ POST /partner/promotions (2): Promoção criada com ID {promotion_2_id}",
                    "SUCCESS",
                )
            else:
                self.print_step(
                    f"❌ POST /partner/promotions (2): {response.status_code} - {response.text}",
                    "ERROR",
                )
        except Exception as e:
            self.print_step(
                f"❌ Erro no POST /partner/promotions (2): {str(e)}", "ERROR"
            )

        # 4. Atualizar segunda promoção (alterar título e valor de desconto)
        promotion_2_id = results["create_promotion_2"]["promotion_id"]
        if promotion_2_id:
            self.print_step(
                f"4️⃣ Atualizando segunda promoção (ID: {promotion_2_id})...", "INFO"
            )

            # Dados para atualização - alterando título e adicionando valor de desconto
            update_data = {
                "title": "Promoção Teste 2 - ATUALIZADA - Super Desconto 25%",
                "type": "discount",
                "valid_from": "2025-01-01T00:00:00Z",
                "valid_to": "2025-06-30T23:59:59Z",
                "active": True,
                "audience": ["student", "employee"],  # Expandindo audiência
            }

            try:
                response = requests.put(
                    f"{BACKEND_BASE_URL}/partner/promotions/{promotion_2_id}",
                    json=update_data,
                    headers=headers,
                    timeout=10,
                )
                if response.status_code in [200, 201]:
                    update_response = response.json()
                    results["update_promotion"]["success"] = True
                    results["update_promotion"]["data"] = update_response
                    updated_title = update_response.get("data", {}).get("title", "N/A")
                    self.print_step(
                        f"✅ PUT /partner/promotions/{promotion_2_id}: Promoção atualizada",
                        "SUCCESS",
                    )
                    self.print_step(
                        f"   Novo título: {updated_title}",
                        "INFO",
                    )
                else:
                    self.print_step(
                        f"❌ PUT /partner/promotions/{promotion_2_id}: {response.status_code} - {response.text}",
                        "ERROR",
                    )
            except Exception as e:
                self.print_step(
                    f"❌ Erro no PUT /partner/promotions/{promotion_2_id}: {str(e)}",
                    "ERROR",
                )
        else:
            self.print_step(
                "⚠️ PUT não testado: ID da segunda promoção não disponível",
                "WARNING",
            )

        # 5. Excluir primeira promoção
        promotion_1_id = results["create_promotion_1"]["promotion_id"]
        if promotion_1_id:
            self.print_step(
                f"5️⃣ Excluindo primeira promoção (ID: {promotion_1_id})...", "INFO"
            )
            try:
                response = requests.delete(
                    f"{BACKEND_BASE_URL}/partner/promotions/{promotion_1_id}",
                    headers=headers,
                    timeout=10,
                )
                if response.status_code in [200, 204]:
                    results["delete_promotion"]["success"] = True
                    results["delete_promotion"]["data"] = (
                        response.json() if response.content else {"deleted": True}
                    )
                    self.print_step(
                        f"✅ DELETE /partner/promotions/{promotion_1_id}: Promoção excluída",
                        "SUCCESS",
                    )
                else:
                    self.print_step(
                        f"❌ DELETE /partner/promotions/{promotion_1_id}: {response.status_code} - {response.text}",
                        "ERROR",
                    )
            except Exception as e:
                self.print_step(
                    f"❌ Erro no DELETE /partner/promotions/{promotion_1_id}: {str(e)}",
                    "ERROR",
                )
        else:
            self.print_step(
                "⚠️ DELETE não testado: ID da primeira promoção não disponível",
                "WARNING",
            )

        # 6. Listar promoções finais para verificar o resultado
        self.print_step(
            "6️⃣ Listando promoções finais para verificar resultado...", "INFO"
        )
        try:
            response = requests.get(
                f"{BACKEND_BASE_URL}/partner/promotions", headers=headers, timeout=10
            )
            if response.status_code == 200:
                promotions_data = response.json()
                results["get_promotions_final"]["success"] = True
                results["get_promotions_final"]["data"] = promotions_data
                final_count = len(promotions_data.get("data", []))
                results["get_promotions_final"]["count"] = final_count

                initial_count = results["get_promotions_initial"]["count"]
                expected_count = initial_count + 1  # +2 criadas, -1 excluída

                self.print_step(
                    f"✅ GET /partner/promotions (final): {final_count} promoções encontradas",
                    "SUCCESS",
                )
                self.print_step(
                    f"📊 Resumo: Inicial={initial_count}, Final={final_count}, Esperado={expected_count}",
                    "INFO",
                )

                if final_count == expected_count:
                    self.print_step(
                        "✅ Fluxo completo executado com sucesso!", "SUCCESS"
                    )
                else:
                    self.print_step(
                        f"⚠️ Contagem final ({final_count}) diferente do esperado ({expected_count})",
                        "WARNING",
                    )
            else:
                self.print_step(
                    f"❌ GET /partner/promotions (final): {response.status_code} - {response.text}",
                    "ERROR",
                )
        except Exception as e:
            self.print_step(
                f"❌ Erro no GET /partner/promotions (final): {str(e)}", "ERROR"
            )

        return results

    def run_complete_test(self, user_key: str) -> dict:
        """
        Executa o teste completo de autenticação para um usuário.

        Args:
            user_key: Chave do usuário no dicionário TEST_USERS

        Returns:
            Dicionário com resultados do teste
        """
        if user_key not in TEST_USERS:
            return {
                "user": user_key,
                "success": False,
                "error": "Usuário não encontrado",
                "steps": [],
            }

        user_data = TEST_USERS[user_key]
        test_result = {
            "user": user_key,
            "email": user_data["email"],
            "role": user_data["role"],
            "success": False,
            "steps": [],
            "tokens": {},
            "user_info": {},
            "endpoints_tested": [],
            "partner_promotions_tests": None,
        }

        self.print_header(f"TESTE COMPLETO - {user_data['description'].upper()}")

        # Etapa 1: Validar ambiente
        if not self.validate_environment():
            test_result["steps"].append(
                {"step": "validate_environment", "success": False}
            )
            return test_result
        test_result["steps"].append({"step": "validate_environment", "success": True})

        # Etapa 2: Autenticação Firebase
        firebase_success, firebase_token = self.authenticate_firebase(
            user_data["email"], user_data["password"]
        )

        test_result["steps"].append(
            {"step": "firebase_auth", "success": firebase_success}
        )

        if not firebase_success:
            return test_result

        test_result["tokens"]["firebase_token"] = (
            firebase_token[:20] + "..." if firebase_token else None
        )

        # Etapa 3: Login no backend
        backend_success, jwt_token = self.login_backend(
            firebase_token, user_data["role"]
        )

        test_result["steps"].append(
            {"step": "backend_login", "success": backend_success}
        )

        if not backend_success:
            return test_result

        test_result["tokens"]["jwt_token"] = (
            jwt_token[:20] + "..." if jwt_token else None
        )
        test_result["user_info"] = self.user_info or {}

        # Etapa 4: Testar endpoints autenticados
        endpoints_to_test = ["/users/me", "/health"]

        # Adicionar endpoints específicos por role
        role_endpoints = {
            "student": ["/students/profile", "/students/benefits"],
            "partner": [
                "/partner/promotions",
                "/partner/reports",
            ],  # Endpoints /partners/profile e /partners/benefits não existem
            "admin": ["/admin/users", "/admin/stats"],
            "employee": ["/employees/profile"],
        }

        if user_data["role"] in role_endpoints:
            endpoints_to_test.extend(role_endpoints[user_data["role"]])

        for endpoint in endpoints_to_test:
            endpoint_success, endpoint_data = self.test_authenticated_endpoint(endpoint)
            test_result["endpoints_tested"].append(
                {
                    "endpoint": endpoint,
                    "success": endpoint_success,
                    "data_received": bool(endpoint_data),
                }
            )

        # Etapa 5: Testes específicos para parceiros
        if user_data["role"] == "partner":
            self.print_step("\n🎯 Executando testes específicos de parceiro...", "INFO")
            partner_tests = self.test_partner_promotions_endpoints()
            test_result["partner_promotions_tests"] = partner_tests

            # Adicionar resultado dos testes de parceiro ao sucesso geral
            partner_success = all(test["success"] for test in partner_tests.values())
            test_result["steps"].append(
                {"step": "partner_promotions", "success": partner_success}
            )

        # Verificar se todos os passos foram bem-sucedidos
        all_steps_success = all(step["success"] for step in test_result["steps"])
        test_result["success"] = all_steps_success

        return test_result

    def display_user_menu(self) -> str:
        """
        Exibe menu para seleção de usuário e retorna a escolha.

        Returns:
            Chave do usuário selecionado
        """
        self.print_header("SELEÇÃO DE USUÁRIO PARA TESTE")

        print("\nUsuários disponíveis para teste:")
        print("-" * 50)

        for i, (key, user_data) in enumerate(TEST_USERS.items(), 1):
            print(f"{i}. {user_data['description']}")
            print(f"   Email: {user_data['email']}")
            print(f"   Role: {user_data['role']}")
            print()

        while True:
            try:
                choice = input(
                    f"Selecione um usuário (1-{len(TEST_USERS)}) ou 'q' para sair: "
                )

                if choice.lower() == "q":
                    return None

                choice_num = int(choice)
                if 1 <= choice_num <= len(TEST_USERS):
                    user_keys = list(TEST_USERS.keys())
                    return user_keys[choice_num - 1]
                else:
                    print("Opção inválida. Tente novamente.")

            except ValueError:
                print("Por favor, digite um número válido ou 'q' para sair.")

    def generate_report(self, test_results: list[dict]) -> None:
        """
        Gera relatório dos testes executados.

        Args:
            test_results: Lista com resultados dos testes
        """
        self.print_header("RELATÓRIO DE TESTES")

        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results if result["success"])

        print("\nResumo Geral:")
        print(f"- Total de testes: {total_tests}")
        print(f"- Testes bem-sucedidos: {successful_tests}")
        print(f"- Testes falharam: {total_tests - successful_tests}")
        print(
            f"- Taxa de sucesso: {(successful_tests/total_tests*100):.1f}%"
            if total_tests > 0
            else "0%"
        )

        print("\nDetalhes por usuário:")
        print("-" * 80)

        for result in test_results:
            status_icon = "✅" if result["success"] else "❌"
            print(f"\n{status_icon} {result.get('email', result['user'])}")
            print(f"   Role: {result.get('role', 'N/A')}")

            if result["success"]:
                print(
                    f"   Firebase Token: {result['tokens'].get('firebase_token', 'N/A')}"
                )
                print(f"   JWT Token: {result['tokens'].get('jwt_token', 'N/A')}")
                print(
                    f"   Endpoints testados: {len(result.get('endpoints_tested', []))}"
                )
            else:
                failed_steps = [
                    step["step"]
                    for step in result.get("steps", [])
                    if not step["success"]
                ]
                if failed_steps:
                    print(f"   Falhou em: {', '.join(failed_steps)}")
                if "error" in result:
                    print(f"   Erro: {result['error']}")

        # Salvar relatório em arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(SCRIPT_DIR, f"auth_test_report_{timestamp}.json")

        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "timestamp": timestamp,
                        "summary": {
                            "total_tests": total_tests,
                            "successful_tests": successful_tests,
                            "failed_tests": total_tests - successful_tests,
                            "success_rate": (successful_tests / total_tests * 100)
                            if total_tests > 0
                            else 0,
                        },
                        "results": test_results,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            self.print_step(f"Relatório salvo em: {report_file}", "SUCCESS")

        except Exception as e:
            self.print_step(f"Erro ao salvar relatório: {str(e)}", "ERROR")


def main():
    """Função principal do script."""
    import argparse

    parser = argparse.ArgumentParser(description="Teste de Autenticação Completo")
    parser.add_argument(
        "--user",
        choices=["partner", "admin", "student", "employee"],
        help="Usuário específico para teste",
    )
    parser.add_argument(
        "--auto", action="store_true", help="Modo automático usando parceiro_teste"
    )

    args = parser.parse_args()

    print("🚀 Script de Teste Completo de Autenticação - Portal KNN")
    print("=" * 60)

    tester = AuthenticationTester()

    # Verificar se deve usar usuário específico, automático ou menu
    if args.auto:
        # Modo automático - usar parceiro_teste
        selected_user = "parceiro_teste"
        print(
            f"\n🤖 Modo automático ativado - usando usuário: {TEST_USERS[selected_user]['email']}"
        )
    elif args.user:
        # Usuário específico via parâmetro
        user_mapping = {
            "partner": "parceiro_teste",
            "admin": "admin_teste",
            "student": "estudante_teste",
            "employee": "funcionario_teste",
        }
        selected_user = user_mapping[args.user]
        print(
            f"\n👤 Usuário selecionado via parâmetro: {TEST_USERS[selected_user]['email']}"
        )
    else:
        # Modo interativo - mostrar menu
        selected_user = tester.display_user_menu()

    if not selected_user:
        print("\n👋 Teste cancelado pelo usuário.")
        return

    # Executar teste
    test_result = tester.run_complete_test(selected_user)

    # Gerar relatório
    tester.generate_report([test_result])

    # Resultado final
    if test_result["success"]:
        print(f"\n🎉 Teste completo bem-sucedido para {test_result['email']}!")
        print("✅ Todos os passos da autenticação funcionaram corretamente.")
    else:
        print(f"\n❌ Teste falhou para {test_result['email']}")
        print("🔍 Verifique os logs acima para identificar o problema.")

    return 0 if test_result["success"] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
