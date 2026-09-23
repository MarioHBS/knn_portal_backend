"""
Configurações e variáveis de ambiente para o Portal de Benefícios KNN.
"""

import json
import os
from pathlib import Path

# Carregar variáveis do arquivo .env se existir
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv não está instalado, continuar sem carregar .env
    pass

# --- Configurações de Ambiente ---
_environment_env = os.getenv("ENVIRONMENT")
_environment_is_explicit = _environment_env is not None
ENVIRONMENT = _environment_env or "development"
IS_PRODUCTION = ENVIRONMENT == "production"

# TESTING_MODE só pode ser habilitado explicitamente. Nunca habilitar o modo
# mock por inferência do ambiente: um deploy sem configuração deve falhar
# fechado, não iniciar com autenticação desabilitada.
_testing_mode_env = os.getenv("TESTING_MODE")
if _testing_mode_env is None:
    TESTING_MODE = False
else:
    TESTING_MODE = _testing_mode_env.lower() in ("true", "1", "t", "yes", "y")

_running_on_cloud_run = "K_SERVICE" in os.environ
if TESTING_MODE and (IS_PRODUCTION or _running_on_cloud_run):
    raise RuntimeError(
        "TESTING_MODE não pode ser habilitado em produção ou no Cloud Run"
    )
if _running_on_cloud_run and not _environment_is_explicit:
    raise RuntimeError(
        "ENVIRONMENT deve ser definido explicitamente quando K_SERVICE estiver presente"
    )

# --- Configurações da API ---
API_VERSION = "v1"
API_TITLE = "Portal de Benefícios KNN API"
API_DESCRIPTION = "API para o Portal de Benefícios KNN, permitindo que alunos da KNN Idiomas acessem promoções exclusivas de parceiros comerciais."
DEBUG = not IS_PRODUCTION
PORT = int(os.getenv("PORT", "8080"))

# --- Configurações de Banco de Dados ---
FIRESTORE_PROJECT = os.getenv("FIRESTORE_PROJECT", "knn-benefits")

# Define o banco de dados do Firestore com base no ambiente
# Em produção, usa 'knn-benefits'; em desenvolvimento, usa '(default)'
FIRESTORE_DATABASE_NAME = "knn-benefits"  # if IS_PRODUCTION else "(default)"

# Compatibilidade com módulos que utilizam múltiplos bancos Firestore
_firestore_databases_env = os.getenv("FIRESTORE_DATABASES")
if _firestore_databases_env:
    try:
        FIRESTORE_DATABASES_LIST = json.loads(_firestore_databases_env)
        if not isinstance(FIRESTORE_DATABASES_LIST, list):
            raise ValueError("FIRESTORE_DATABASES must be a JSON array")
    except Exception:
        FIRESTORE_DATABASES_LIST = ["(default)", "knn-benefits"]
else:
    FIRESTORE_DATABASES_LIST = ["(default)", "knn-benefits"]

_firestore_database_env = os.getenv("FIRESTORE_DATABASE")
if _firestore_database_env is not None:
    try:
        FIRESTORE_DATABASE = int(_firestore_database_env)
    except ValueError:
        FIRESTORE_DATABASE = 1 if IS_PRODUCTION else 0
else:
    FIRESTORE_DATABASE = 1 if IS_PRODUCTION else 0

# Garantir índice válido
if (
    not isinstance(FIRESTORE_DATABASE, int)
    or FIRESTORE_DATABASE < 0
    or len(FIRESTORE_DATABASES_LIST) <= FIRESTORE_DATABASE
):
    FIRESTORE_DATABASE = 0

CURRENT_FIRESTORE_DATABASE = FIRESTORE_DATABASES_LIST[FIRESTORE_DATABASE]

# --- Configurações de CORS ---
if IS_PRODUCTION:
    CORS_ORIGINS = [
        "https://knn-journeyclub.vercel.app",
        "https://journeyclub.com.br/",
        "https://www.journeyclub.com.br/",
    ]
else:
    CORS_ORIGINS = [
        "https://portal.knnidiomas.com.br",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]

# --- Configurações de Credenciais ---
# A variável GOOGLE_APPLICATION_CREDENTIALS é lida automaticamente pelo Google Cloud
# e não precisa ser definida explicitamente no código.
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
FIRESTORE_SERVICE_ACCOUNT_KEY = os.getenv("FIRESTORE_SERVICE_ACCOUNT_KEY")

# --- Configurações do PostgreSQL (Contingência) ---
POSTGRES_ENABLED = os.getenv("POSTGRES_ENABLED", "false").lower() in ("true", "1", "t")
POSTGRES_CONNECTION_STRING = os.getenv(
    "POSTGRES_CONNECTION_STRING",
    "postgresql://postgres:postgres@localhost:5432/knn_portal",
)

# --- Configurações de Segurança ---
CNPJ_HASH_SALT = os.getenv("CNPJ_HASH_SALT", "knn-dev-salt")
CPF_HASH_SALT = os.getenv("CPF_HASH_SALT", "knn-dev-cpf-salt")

# --- Configurações de Circuit Breaker ---
CIRCUIT_BREAKER_THRESHOLD = 3
CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutos

# --- Configurações de Rate Limit ---
RATE_LIMIT_REDEEM = "5/minute"

# --- Configurações do Firebase Storage ---
FIREBASE_STORAGE_BUCKET = os.getenv(
    "FIREBASE_STORAGE_BUCKET", "knn-benefits.firebasestorage.app"
)

# --- Modo de Operação ---
# 'normal' usa o Firestore como primário
# 'degraded' usa o PostgreSQL como primário
MODE = os.getenv("MODE", "normal")

# --- Configurações de Serviço de Email ---
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SERVICE_ENABLED = os.getenv("EMAIL_SERVICE_ENABLED", "false").lower() in (
    "true",
    "1",
    "t",
)
