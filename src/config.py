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
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Compatibilidade: manter TESTING_MODE disponível para módulos existentes.
# Se não definido explicitamente, assume True em desenvolvimento e False em produção.
_testing_mode_env = os.getenv("TESTING_MODE")
if _testing_mode_env is None:
    TESTING_MODE = not IS_PRODUCTION
else:
    TESTING_MODE = _testing_mode_env.lower() in ("true", "1", "t", "yes", "y")

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

# --- Configurações de Autenticação ---
JWKS_URL = os.getenv("JWKS_URL", "https://auth.knnidiomas.com.br/.well-known/jwks.json")
JWKS_CACHE_TTL = int(os.getenv("JWKS_CACHE_TTL", "600"))  # 10 minutos
JWT_ALGORITHM = "RS256"
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "knn-dev-jwt-secret-key-change-in-production"
)

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
