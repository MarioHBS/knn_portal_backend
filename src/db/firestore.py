"""
Implementação da camada de acesso ao Firestore.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, List, Optional, Any, Union
import uuid
from datetime import datetime

from src.config import FIRESTORE_PROJECT
from src.utils import logger

# Inicializar o Firestore
try:
    # Em ambiente de produção, usamos credenciais padrão
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': FIRESTORE_PROJECT,
    })
    db = firestore.client()
    logger.info("Firestore inicializado com sucesso")
except Exception as e:
    # Em ambiente de desenvolvimento/teste, podemos usar um emulador
    logger.warning(f"Erro ao inicializar Firestore com credenciais padrão: {str(e)}")
    try:
        firebase_admin.initialize_app(options={
            'projectId': FIRESTORE_PROJECT,
        })
        db = firestore.client()
        logger.info("Firestore inicializado com emulador")
    except Exception as e:
        logger.error(f"Erro ao inicializar Firestore com emulador: {str(e)}")
        db = None

class FirestoreClient:
    """Cliente para acesso ao Firestore."""
    
    @staticmethod
    async def get_document(collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém um documento do Firestore.
        """
        if not db:
            logger.error("Firestore não inicializado")
            return None
        
        try:
            doc_ref = db.collection(collection).document(doc_id)
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
        filters: Optional[List[tuple]] = None, 
        order_by: Optional[List[tuple]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Consulta documentos no Firestore com filtros e ordenação.
        
        Args:
            collection: Nome da coleção
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
            # Iniciar query
            query = db.collection(collection)
            
            # Aplicar filtros
            if filters:
                for field, op, value in filters:
                    query = query.where(field, op, value)
            
            # Contar total (antes de aplicar limit/offset)
            total_query = query
            total_docs = len([d for d in total_query.stream()])
            
            # Aplicar ordenação
            if order_by:
                for field, direction in order_by:
                    query = query.order_by(field, direction=direction)
            
            # Aplicar paginação
            if offset > 0:
                # No Firestore, precisamos usar cursor para offset
                # Simplificação: obtemos todos e aplicamos slice
                all_docs = [d for d in query.limit(offset + limit).stream()]
                docs = all_docs[offset:offset + limit]
            else:
                docs = [d for d in query.limit(limit).stream()]
            
            # Converter para dicionários
            items = [{**doc.to_dict(), "id": doc.id} for doc in docs]
            
            return {
                "items": items,
                "total": total_docs,
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            logger.error(f"Erro ao consultar documentos em {collection}: {str(e)}")
            raise
    
    @staticmethod
    async def create_document(collection: str, data: Dict[str, Any], doc_id: Optional[str] = None) -> Dict[str, Any]:
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
    async def update_document(collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
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
    async def batch_operation(operations: List[Dict[str, Any]]) -> bool:
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
