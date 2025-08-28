"""
Configurações e variáveis de ambiente para o Portal de Benefícios KNN.
"""
import os

# Configurações da API
API_VERSION = "v1"
API_TITLE = "Portal de Benefícios KNN API"
API_DESCRIPTION = "API para o Portal de Benefícios KNN, permitindo que alunos da KNN Idiomas acessem promoções exclusivas de parceiros comerciais."

# Configurações de ambiente
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8080"))

# Configurações de CORS
CORS_ORIGINS = ["https://portal.knnidiomas.com.br", "http://localhost:5173"]

# Configurações de autenticação
JWKS_URL = os.getenv("JWKS_URL", "https://auth.knnidiomas.com.br/.well-known/jwks.json")
JWKS_CACHE_TTL = int(os.getenv("JWKS_CACHE_TTL", "600"))  # 10 minutos em segundos
JWT_ALGORITHM = "RS256"

# Configurações de banco de dados
FIRESTORE_PROJECT = os.getenv("FIRESTORE_PROJECT", "knn-portal-dev")
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

# Modo de operação
MODE = os.getenv("MODE", "normal")  # normal ou degraded
