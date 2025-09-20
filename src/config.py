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

# Configurações da API
API_VERSION = "v1"
API_TITLE = "Portal de Benefícios KNN API"
API_DESCRIPTION = "API para o Portal de Benefícios KNN, permitindo que alunos da KNN Idiomas acessem promoções exclusivas de parceiros comerciais."

# Configurações de ambiente
KNN_USE_TEST_DATABASE = os.getenv("KNN_USE_TEST_DATABASE", "False").lower() in (
    "true",
    "1",
    "t",
)
TESTING_MODE = os.getenv("TESTING_MODE", "False").lower() in ("true", "1", "t")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8080"))

# Configurações de CORS
CORS_ORIGINS = [
    "https://portal.knnidiomas.com.br",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]


# Configurações de autenticação
JWKS_URL = os.getenv("JWKS_URL", "https://auth.knnidiomas.com.br/.well-known/jwks.json")
JWKS_CACHE_TTL = int(os.getenv("JWKS_CACHE_TTL", "600"))  # 10 minutos em segundos
JWT_ALGORITHM = "RS256"
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "knn-dev-jwt-secret-key-change-in-production"
)

# Configurações do banco de dados
FIRESTORE_PROJECT = os.getenv("FIRESTORE_PROJECT", "knn-benefits")

# Configurações de autenticação do Firestore
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
FIRESTORE_SERVICE_ACCOUNT_KEY = os.getenv("FIRESTORE_SERVICE_ACCOUNT_KEY")

# Configurações de múltiplos bancos Firestore
FIRESTORE_DATABASES = os.getenv("FIRESTORE_DATABASES", '["(default)","knn-benefits"]')
FIRESTORE_DATABASE = int(os.getenv("FIRESTORE_DATABASE", "0"))

# Parse da lista de bancos de dados
try:
    FIRESTORE_DATABASES_LIST = json.loads(FIRESTORE_DATABASES)
except json.JSONDecodeError:
    FIRESTORE_DATABASES_LIST = ["(default)", "knn-benefits"]

# Seleção do banco atual baseado no índice
if 0 <= FIRESTORE_DATABASE < len(FIRESTORE_DATABASES_LIST):
    CURRENT_FIRESTORE_DATABASE = FIRESTORE_DATABASES_LIST[FIRESTORE_DATABASE]
else:
    CURRENT_FIRESTORE_DATABASE = FIRESTORE_DATABASES_LIST[0]
POSTGRES_CONNECTION_STRING = os.getenv(
    "POSTGRES_CONNECTION_STRING",
    "postgresql://postgres:postgres@localhost:5432/knn_portal",
)

# Configurações de segurança
CNPJ_HASH_SALT = os.getenv("CNPJ_HASH_SALT", "knn-dev-salt")
CPF_HASH_SALT = os.getenv("CPF_HASH_SALT", "knn-dev-cpf-salt")

# Configurações de circuit breaker
CIRCUIT_BREAKER_THRESHOLD = (
    3  # Número de falhas consecutivas para ativar o circuit breaker
)
CIRCUIT_BREAKER_TIMEOUT = 300  # Tempo em segundos para tentar novamente o Firestore

# Configurações de rate limit
RATE_LIMIT_REDEEM = "5/minute"  # 5 requisições por minuto para /partner/redeem

# Configurações do Firebase Storage
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "knn-benefits.firebasestorage.app")

# Modo de operação
MODE = os.getenv("MODE", "normal")  # normal ou degraded
