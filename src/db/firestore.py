"""
Implementação da camada de acesso ao Firestore.
"""

import json
import uuid
from typing import Any

from google.auth import default
from google.cloud import firestore
from google.cloud.firestore import Client
from google.oauth2 import service_account

from src.config import (
    CURRENT_FIRESTORE_DATABASE,
    FIRESTORE_DATABASE,
    FIRESTORE_DATABASES_LIST,
    FIRESTORE_PROJECT,
    FIRESTORE_SERVICE_ACCOUNT_KEY,
    GOOGLE_APPLICATION_CREDENTIALS,
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
                credentials = service_account.Credentials.from_service_account_info(service_account_info)
                if not project_id:
                    project_id = service_account_info.get('project_id')
                logger.info("Usando service account key do ambiente")
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar FIRESTORE_SERVICE_ACCOUNT_KEY: {e}")
                credentials, project_id = default()
        elif GOOGLE_APPLICATION_CREDENTIALS:
            # Usar arquivo de service account key
            try:
                credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
                with open(GOOGLE_APPLICATION_CREDENTIALS) as f:
                    service_account_info = json.load(f)
                    if not project_id:
                        project_id = service_account_info.get('project_id')
                logger.info(f"Usando service account key do arquivo: {GOOGLE_APPLICATION_CREDENTIALS}")
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
                        database=database_name
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
            doc_ref = fs_doc(collection, doc_id, tenant_id)
            doc = doc_ref.get()
            if doc.exists:
                return {**doc.to_dict(), "id": doc.id}
            return None
        except Exception as e:
            logger.error(f"Erro ao obter documento {collection}/{doc_id}: {str(e)}")
            raise

    @staticmethod
    async def query_documents(
        collection: str,
        *,
        tenant_id: str,
        filters: list[tuple] | None = None,
        order_by: list[tuple] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Consulta documentos no Firestore com filtros e ordenação.

        Args:
            collection: Nome da coleção
            tenant_id: ID do tenant para filtrar os documentos
            filters: Lista de tuplas (campo, operador, valor)
            order_by: Lista de tuplas (campo, direção)
            limit: Limite de documentos
            offset: Offset para paginação

        Returns:
            Dict com items, total, limit e offset
        """
        if not db:
            logger.error("Firestore não inicializado")
            return {"items": [], "total": 0, "limit": limit, "offset": offset}

        try:
            # Iniciar query com filtro de tenant_id obrigatório
            query = db.collection(collection).where("tenant_id", "==", tenant_id)

            # Aplicar filtros adicionais
            if filters:
                for field, op, value in filters:
                    query = query.where(field, op, value)

            # Contar total (antes de aplicar limit/offset)
            total_query = query
            total_docs = len(list(total_query.stream()))

            # Aplicar ordenação
            if order_by:
                for field, direction in order_by:
                    query = query.order_by(field, direction=direction)

            # Aplicar paginação
            if offset > 0:
                # No Firestore, precisamos usar cursor para offset
                # Simplificação: obtemos todos e aplicamos slice
                all_docs = list(query.limit(offset + limit).stream())
                docs = all_docs[offset : offset + limit]
            else:
                docs = list(query.limit(limit).stream())

            # Converter para dicionários
            items = [{**doc.to_dict(), "id": doc.id} for doc in docs]

            return {
                "items": items,
                "total": total_docs,
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"Erro ao consultar documentos em {collection}: {str(e)}")
            raise

    @staticmethod
    async def create_document(
        collection: str, data: dict[str, Any], doc_id: str | None = None
    ) -> dict[str, Any]:
        """
        Cria um documento no Firestore.
        """
        if not db:
            logger.error("Firestore não inicializado")
            return None

        try:
            # Gerar ID se não fornecido
            if not doc_id:
                doc_id = str(uuid.uuid4())

            # Adicionar timestamp de criação
            data["created_at"] = firestore.SERVER_TIMESTAMP

            # Criar documento
            doc_ref = db.collection(collection).document(doc_id)
            doc_ref.set(data)

            # Obter documento criado
            doc = doc_ref.get()
            return {**doc.to_dict(), "id": doc.id}
        except Exception as e:
            logger.error(f"Erro ao criar documento em {collection}: {str(e)}")
            raise

    @staticmethod
    async def update_document(
        collection: str, doc_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Atualiza um documento no Firestore.
        """
        if not db:
            logger.error("Firestore não inicializado")
            return None

        try:
            # Adicionar timestamp de atualização
            data["updated_at"] = firestore.SERVER_TIMESTAMP

            # Atualizar documento
            doc_ref = db.collection(collection).document(doc_id)
            doc_ref.update(data)

            # Obter documento atualizado
            doc = doc_ref.get()
            return {**doc.to_dict(), "id": doc.id}
        except Exception as e:
            logger.error(f"Erro ao atualizar documento {collection}/{doc_id}: {str(e)}")
            raise

    @staticmethod
    async def delete_document(collection: str, doc_id: str) -> bool:
        """
        Remove um documento do Firestore.
        """
        if not db:
            logger.error("Firestore não inicializado")
            return False

        try:
            db.collection(collection).document(doc_id).delete()
            return True
        except Exception as e:
            logger.error(f"Erro ao remover documento {collection}/{doc_id}: {str(e)}")
            raise

    @staticmethod
    async def batch_operation(operations: list[dict[str, Any]]) -> bool:
        """
        Executa operações em lote no Firestore.

        Args:
            operations: Lista de operações no formato:
                {
                    "operation": "create|update|delete",
                    "collection": "nome_colecao",
                    "doc_id": "id_documento",
                    "data": {...}  # Apenas para create/update
                }
        """
        if not db:
            logger.error("Firestore não inicializado")
            return False

        try:
            batch = db.batch()

            for op in operations:
                operation = op.get("operation")
                collection = op.get("collection")
                doc_id = op.get("doc_id")
                data = op.get("data", {})

                doc_ref = db.collection(collection).document(doc_id)

                if operation == "create":
                    data["created_at"] = firestore.SERVER_TIMESTAMP
                    batch.set(doc_ref, data)
                elif operation == "update":
                    data["updated_at"] = firestore.SERVER_TIMESTAMP
                    batch.update(doc_ref, data)
                elif operation == "delete":
                    batch.delete(doc_ref)

            batch.commit()
            return True
        except Exception as e:
            logger.error(f"Erro ao executar operações em lote: {str(e)}")
            raise


# Instância do cliente Firestore
firestore_client = FirestoreClient()
