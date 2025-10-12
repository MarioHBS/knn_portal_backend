"""
Configuração do cliente Firebase Storage.

Este módulo inicializa e gerencia a conexão com o Firebase Storage,
usando as mesmas credenciais configuradas para o Firestore.
"""

import json

from google.auth import default
from google.cloud import storage
from google.oauth2 import service_account

from src.config import (
    FIREBASE_STORAGE_BUCKET,
    FIRESTORE_PROJECT,
    FIRESTORE_SERVICE_ACCOUNT_KEY,
    GOOGLE_APPLICATION_CREDENTIALS,
    TESTING_MODE,
)
from src.utils.logging import logger

# Cliente global do Storage
storage_client = None


def initialize_storage_client():
    """Inicializa cliente do Firebase Storage."""
    global storage_client

    try:
        # Configurar credenciais baseado nas variáveis de ambiente
        credentials = None
        project_id = FIRESTORE_PROJECT

        if FIRESTORE_SERVICE_ACCOUNT_KEY:
            # Usar service account key como JSON string
            try:
                service_account_info = json.loads(FIRESTORE_SERVICE_ACCOUNT_KEY)
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info
                )
                if not project_id:
                    project_id = service_account_info.get("project_id")
                logger.info("Storage: Usando service account key do ambiente")
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar FIRESTORE_SERVICE_ACCOUNT_KEY: {e}")
                credentials, project_id = default()
        elif GOOGLE_APPLICATION_CREDENTIALS:
            # Usar arquivo de service account key
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    GOOGLE_APPLICATION_CREDENTIALS
                )
                with open(GOOGLE_APPLICATION_CREDENTIALS) as f:
                    service_account_info = json.load(f)
                    if not project_id:
                        project_id = service_account_info.get("project_id")
                logger.info(
                    f"Storage: Usando service account key do arquivo: {GOOGLE_APPLICATION_CREDENTIALS}"
                )
            except Exception as e:
                logger.error(f"Erro ao carregar service account key: {e}")
                credentials, project_id = default()
        else:
            # Usar credenciais padrão (ADC)
            credentials, detected_project = default()
            if not project_id:
                project_id = detected_project
            logger.info("Storage: Usando credenciais padrão (ADC)")

        # Inicializar cliente do Storage
        storage_client = storage.Client(project=project_id, credentials=credentials)

        # Verificar se o bucket existe
        bucket_name = FIREBASE_STORAGE_BUCKET
        if not bucket_name:
            raise ValueError("FIREBASE_STORAGE_BUCKET não configurado")

        # Testar acesso ao bucket
        bucket = storage_client.bucket(bucket_name)
        bucket.reload()  # Verifica se o bucket existe e é acessível

        logger.info(f"Storage: Cliente inicializado para projeto {project_id}")
        logger.info(f"Storage: Bucket configurado: {bucket_name}")

        return storage_client

    except Exception as e:
        logger.error(f"Erro ao inicializar cliente do Storage: {e}")
        raise


def get_storage_client():
    """Retorna o cliente do Storage, inicializando se necessário."""
    global storage_client
    if storage_client is None:
        storage_client = initialize_storage_client()
    return storage_client


def get_bucket():
    """
    Obtém o bucket configurado do Firebase Storage.

    Returns:
        Bucket: Instância do bucket configurado
    """
    client = get_storage_client()
    bucket_name = FIREBASE_STORAGE_BUCKET
    logger.info(f"Storage: Bucket configurado: {bucket_name}")
    return client.bucket(bucket_name)


# Inicializar automaticamente quando o módulo for importado,
# evitando inicialização em modo de teste para não depender de serviços externos.
if not TESTING_MODE:
    try:
        initialize_storage_client()
    except Exception as e:
        logger.warning(f"Falha na inicialização automática do Storage: {e}")
