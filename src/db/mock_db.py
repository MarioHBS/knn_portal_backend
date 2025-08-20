"""
Script para simular o comportamento do Firestore e PostgreSQL para testes locais.
"""
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Diretório para armazenar dados simulados
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")

# Configuração do circuit breaker simulado
FIRESTORE_FAILURE_MODE = False  # Altere para True para simular falhas no Firestore


class MockFirestore:
    """
    Simulação do Firestore para testes locais.
    """

    @staticmethod
    def get_collection_data(collection: str) -> List[Dict[str, Any]]:
        """
        Obtém dados de uma coleção.
        """
        try:
            file_path = os.path.join(DATA_DIR, f"{collection}.json")
            if os.path.exists(file_path):
                with open(file_path) as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Erro ao ler coleção {collection}: {str(e)}")
            return []

    @staticmethod
    def save_collection_data(collection: str, data: List[Dict[str, Any]]) -> bool:
        """
        Salva dados em uma coleção.
        """
        try:
            file_path = os.path.join(DATA_DIR, f"{collection}.json")
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao salvar coleção {collection}: {str(e)}")
            return False

    @staticmethod
    async def get_document(collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém um documento do Firestore simulado.
        """
        # Simular falha se o modo de falha estiver ativado
        if FIRESTORE_FAILURE_MODE:
            raise Exception("Falha simulada no Firestore")

        # Obter dados da coleção
        items = MockFirestore.get_collection_data(collection)

        # Buscar documento pelo ID
        for item in items:
            if item.get("id") == doc_id:
                return item

        return None

    @staticmethod
    async def query_documents(
        collection: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[List[tuple]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Consulta documentos no Firestore simulado.
        """
        # Simular falha se o modo de falha estiver ativado
        if FIRESTORE_FAILURE_MODE:
            raise Exception("Falha simulada no Firestore")

        # Obter dados da coleção
        items = MockFirestore.get_collection_data(collection)

        # Aplicar filtros
        if filters:
            filtered_items = []
            for item in items:
                match = True
                for field, op, value in filters:
                    item_value = item.get(field)

                    if op == "==" and item_value != value:
                        match = False
                        break
                    elif op == "!=" and item_value == value:
                        match = False
                        break
                    elif op == "<" and (item_value is None or item_value >= value):
                        match = False
                        break
                    elif op == "<=" and (item_value is None or item_value > value):
                        match = False
                        break
                    elif op == ">" and (item_value is None or item_value <= value):
                        match = False
                        break
                    elif op == ">=" and (item_value is None or item_value < value):
                        match = False
                        break

                if match:
                    filtered_items.append(item)

            items = filtered_items

        # Aplicar ordenação
        if order_by:
            for field, direction in reversed(order_by):
                reverse = direction == "DESCENDING"
                items = sorted(items, key=lambda x: x.get(field, ""), reverse=reverse)

        # Contar total
        total = len(items)

        # Aplicar paginação
        items = items[offset : offset + limit]

        return {"items": items, "total": total, "limit": limit, "offset": offset}

    @staticmethod
    async def create_document(
        collection: str, data: Dict[str, Any], doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um documento no Firestore simulado.
        """
        # Simular falha se o modo de falha estiver ativado
        if FIRESTORE_FAILURE_MODE:
            raise Exception("Falha simulada no Firestore")

        # Obter dados da coleção
        items = MockFirestore.get_collection_data(collection)

        # Adicionar timestamp de criação
        data["created_at"] = datetime.now().isoformat()

        # Adicionar documento
        items.append(data)

        # Salvar dados
        MockFirestore.save_collection_data(collection, items)

        return data

    @staticmethod
    async def update_document(
        collection: str, doc_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Atualiza um documento no Firestore simulado.
        """
        # Simular falha se o modo de falha estiver ativado
        if FIRESTORE_FAILURE_MODE:
            raise Exception("Falha simulada no Firestore")

        # Obter dados da coleção
        items = MockFirestore.get_collection_data(collection)

        # Adicionar timestamp de atualização
        data["updated_at"] = datetime.now().isoformat()

        # Buscar e atualizar documento
        updated_item = None
        for i, item in enumerate(items):
            if item.get("id") == doc_id:
                # Atualizar campos
                for key, value in data.items():
                    item[key] = value

                updated_item = item
                items[i] = item
                break

        # Salvar dados
        if updated_item:
            MockFirestore.save_collection_data(collection, items)
            return updated_item

        raise Exception(f"Documento {collection}/{doc_id} não encontrado")

    @staticmethod
    async def delete_document(collection: str, doc_id: str) -> bool:
        """
        Remove um documento do Firestore simulado.
        """
        # Simular falha se o modo de falha estiver ativado
        if FIRESTORE_FAILURE_MODE:
            raise Exception("Falha simulada no Firestore")

        # Obter dados da coleção
        items = MockFirestore.get_collection_data(collection)

        # Buscar e remover documento
        for i, item in enumerate(items):
            if item.get("id") == doc_id:
                items.pop(i)

                # Salvar dados
                MockFirestore.save_collection_data(collection, items)
                return True

        return False


class MockPostgres:
    """
    Simulação do PostgreSQL para testes locais.
    """

    @staticmethod
    async def get_document(table: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém um documento do PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.get_document(table, doc_id)

    @staticmethod
    async def query_documents(
        table: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[List[tuple]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Consulta documentos no PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.query_documents(
            table, filters, order_by, limit, offset
        )

    @staticmethod
    async def create_document(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um documento no PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.create_document(table, data, data.get("id"))

    @staticmethod
    async def update_document(
        table: str, doc_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Atualiza um documento no PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.update_document(table, doc_id, data)

    @staticmethod
    async def delete_document(table: str, doc_id: str) -> bool:
        """
        Remove um documento do PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.delete_document(table, doc_id)


class MockCircuitBreaker:
    """
    Simulação do circuit breaker para testes locais.
    """

    def __init__(self):
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open

    def record_failure(self):
        """
        Registra uma falha no Firestore.
        """
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= 3:  # Threshold = 3
            self.state = "open"
            print(f"Circuit breaker aberto após {self.failures} falhas consecutivas")

    def record_success(self):
        """
        Registra um sucesso no Firestore.
        """
        self.failures = 0
        self.state = "closed"

    def can_execute(self):
        """
        Verifica se o Firestore pode ser acessado.
        """
        if self.state == "closed":
            return True

        if self.state == "open":
            # Verificar se já passou o tempo de timeout (10 segundos para testes)
            if time.time() - self.last_failure_time > 10:
                self.state = "half-open"
                print(
                    "Circuit breaker em estado half-open, tentando Firestore novamente"
                )
                return True
            return False

        # Estado half-open
        return True


# Instâncias globais
mock_firestore = MockFirestore()
mock_postgres = MockPostgres()
mock_circuit_breaker = MockCircuitBreaker()


async def with_mock_circuit_breaker(
    firestore_func, postgres_func, *args, **kwargs
) -> Any:
    """
    Executa uma função com circuit breaker simulado.
    """
    if mock_circuit_breaker.can_execute():
        try:
            # Tentar Firestore
            result = await firestore_func(*args, **kwargs)
            mock_circuit_breaker.record_success()
            return result
        except Exception as e:
            # Registrar falha
            mock_circuit_breaker.record_failure()
            print(f"Erro no Firestore, fazendo fallback para PostgreSQL: {str(e)}")
    else:
        print("Circuit breaker aberto, usando PostgreSQL diretamente")

    # Fallback para PostgreSQL
    try:
        return await postgres_func(*args, **kwargs)
    except Exception as e:
        print(f"Erro no fallback para PostgreSQL: {str(e)}")
        raise


# Função para ativar/desativar modo de falha do Firestore
def toggle_firestore_failure_mode():
    """
    Ativa/desativa o modo de falha do Firestore para testes.
    """
    global FIRESTORE_FAILURE_MODE
    FIRESTORE_FAILURE_MODE = not FIRESTORE_FAILURE_MODE
    print(
        f"Modo de falha do Firestore: {'ATIVADO' if FIRESTORE_FAILURE_MODE else 'DESATIVADO'}"
    )


if __name__ == "__main__":
    print("Módulo de simulação de banco de dados para testes locais.")
    print(
        "Use as classes MockFirestore, MockPostgres e MockCircuitBreaker para testes."
    )
    print(
        "Use a função toggle_firestore_failure_mode() para simular falhas no Firestore."
    )
