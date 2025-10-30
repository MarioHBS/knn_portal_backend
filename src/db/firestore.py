"""
Implementação da camada de acesso ao Firestore.
"""

import asyncio
import json
from typing import Any

from google.auth import default
from google.cloud.firestore import Client
from google.oauth2 import service_account

from src.config import (
    CURRENT_FIRESTORE_DATABASE,
    FIRESTORE_DATABASE,
    FIRESTORE_DATABASES_LIST,
    FIRESTORE_PROJECT,
    FIRESTORE_SERVICE_ACCOUNT_KEY,
)
from src.utils import logger

# Inicializar múltiplos bancos Firestore
db = None
databases = {}  # Dicionário para armazenar conexões com múltiplos bancos


def initialize_firestore_databases():
    """Inicializa conexões com múltiplos bancos Firestore."""
    global db, databases

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
                logger.info("Usando service account key do ambiente")
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar FIRESTORE_SERVICE_ACCOUNT_KEY: {e}")
                credentials, project_id = default()
            except Exception as e:
                logger.error(f"Erro ao carregar service account key: {e}")
                credentials, project_id = default()
        else:
            # Usar credenciais padrão (ADC)
            credentials, detected_project = default()
            if not project_id:
                project_id = detected_project
            logger.info("Usando credenciais padrão (ADC)")

        logger.info(f"Inicializando Firestore para projeto: {project_id}")

        # Inicializar conexões com todos os bancos configurados
        for i, database_name in enumerate(FIRESTORE_DATABASES_LIST):
            try:
                if database_name == "(default)":
                    # Cliente para banco padrão
                    client = Client(project=project_id, credentials=credentials)
                else:
                    # Cliente para banco específico com suporte nativo
                    client = Client(
                        project=project_id,
                        credentials=credentials,
                        database=database_name,
                    )

                databases[database_name] = client
                logger.info(f"Conexão estabelecida com banco: {database_name}")

                # Definir o banco principal baseado na configuração
                if i == FIRESTORE_DATABASE:
                    db = client
                    logger.info(f"Banco principal definido: {database_name}")

            except Exception as e:
                logger.error(f"Erro ao conectar com banco {database_name}: {str(e)}")

        # Se não conseguiu definir o banco principal, usar o primeiro disponível
        if db is None and databases:
            db = list(databases.values())[0]
            logger.warning("Usando primeiro banco disponível como principal")

    except Exception as e:
        logger.error(f"Erro geral ao inicializar Firestore: {str(e)}")
        db = None
        raise


# Inicializar os bancos
initialize_firestore_databases()


def get_database(database_name: str = None):
    """Obtém conexão com um banco específico.

    Args:
        database_name: Nome do banco. Se None, usa o banco principal.

    Returns:
        Cliente Firestore para o banco especificado.
    """
    if database_name is None:
        return db

    if database_name in databases:
        return databases[database_name]

    logger.warning(f"Banco {database_name} não encontrado, usando banco principal")
    return db


def list_available_databases():
    """Lista todos os bancos disponíveis.

    Returns:
        Lista com nomes dos bancos configurados.
    """
    return list(databases.keys())


def get_current_database_name():
    """Obtém o nome do banco atual.

    Returns:
        Nome do banco principal configurado.
    """
    return CURRENT_FIRESTORE_DATABASE


# Helpers multi-tenant


def fs_doc(col: str, id: str, tenant: str):
    return db.collection(col).document(f"{tenant}_{id}")


def fs_query(col: str, tenant: str):
    return db.collection(col).where("tenant_id", "==", tenant)


class FirestoreClient:
    """Cliente para acesso ao Firestore."""

    @staticmethod
    async def get_document(
        collection: str, doc_id: str, tenant_id: str
    ) -> dict[str, Any] | None:
        """
        Obtém um documento do Firestore filtrando por tenant_id.
        """
        if not db:
            logger.error("Firestore não inicializado")
            return None
        try:
            doc_ref = db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            if doc.exists:
                # Verificar se o tenant_id do documento corresponde
                doc_data = doc.to_dict()
                # Verificar tenant_id em system.tenant_id primeiro, depois em tenant_id direto
                doc_tenant_id = doc_data.get("system", {}).get(
                    "tenant_id"
                ) or doc_data.get("tenant_id")
                if doc_tenant_id == tenant_id:
                    return {**doc_data, "id": doc.id}
                else:
                    logger.warning(
                        f"Acesso negado: tenant_id do documento ({doc_tenant_id}) não corresponde ao do usuário ({tenant_id}) em {collection}/{doc_id}"
                    )
                    return None
            return None
        except Exception as e:
            logger.error(f"Erro ao obter documento {collection}/{doc_id}: {str(e)}")
            raise Exception(f"Erro ao obter documento {collection}/{doc_id}") from e

    @staticmethod
    async def query_documents(
        collection: str,
        *,
        tenant_id: str | None = None,
        filters: dict[str, Any] | None = None,
        order_by: str | list[tuple] | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Consulta documentos no Firestore com filtros e ordenação.

        Args:
            collection: Nome da coleção.
            tenant_id: ID do tenant para filtrar os documentos (opcional).
            filters: Dicionário de filtros (campo, valor) para consultas de igualdade.
            order_by: Campo para ordenação ou lista de tuplas (campo, direção).
            limit: Limite de documentos.
            offset: Offset para paginação.

        Returns:
            Uma lista de documentos que correspondem à consulta.
        """
        if not db:
            logger.error("Firestore não inicializado")
            return []

        try:
            query = db.collection(collection)

            # Aplicar filtro de tenant_id se fornecido
            if tenant_id:
                query = query.where("tenant_id", "==", tenant_id)

            # Aplicar filtros adicionais
            if filters:
                if isinstance(filters, dict):
                    for field, value in filters.items():
                        query = query.filter(field, "==", value)
                elif isinstance(filters, list):
                    for f in filters:
                        if len(f) == 3:
                            field, op, value = f
                            query = query.filter(field, op, value)

            # Aplicar ordenação
            if order_by:
                if isinstance(order_by, str):
                    query = query.order_by(order_by)
                elif isinstance(order_by, list):
                    for ob_field, ob_direction in order_by:
                        query = query.order_by(ob_field, direction=ob_direction)

            # Aplicar paginação
            query = query.limit(limit).offset(offset)

            def sync_stream():
                docs = []
                for doc in query.stream():
                    doc_data = doc.to_dict()
                    doc_data["id"] = doc.id
                    docs.append(doc_data)
                return docs

            documents = await asyncio.to_thread(sync_stream)

            return documents
        except Exception as e:
            logger.error(f"Erro ao consultar documentos em {collection}: {str(e)}")
            return []

    @staticmethod
    async def get_collection_count(
        collection: str,
        *,
        tenant_id: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """
        Conta documentos em uma coleção com base em filtros.
        """
        if not db:
            logger.error("Firestore não inicializado")
            return 0

        try:
            query = db.collection(collection)

            # Aplicar filtro de tenant_id se fornecido
            if tenant_id:
                query = query.where("tenant_id", "==", tenant_id)

            # Aplicar filtros adicionais
            if filters:
                if isinstance(filters, dict):
                    for field, value in filters.items():
                        query = query.filter(field, "==", value)
                elif isinstance(filters, list):
                    for f in filters:
                        if len(f) == 3:
                            field, op, value = f
                            query = query.filter(field, op, value)

            # A contagem de documentos é feita com uma agregação
            aggregation_query = query.count()
            result = await asyncio.to_thread(aggregation_query.get)

            # O resultado é uma lista de listas de alias de agregação
            if result and result[0] and hasattr(result[0][0], "value"):
                return result[0][0].value

            return 0
        except Exception as e:
            logger.error(f"Erro ao contar documentos em {collection}: {str(e)}")
            return 0


# Instância do cliente Firestore
firestore_client = FirestoreClient()
