"""
Script para simular o comportamento do Firestore e PostgreSQL para testes locais.
"""

import json
import os
import time
from datetime import datetime
from typing import Any

# Diretório para armazenar dados simulados
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")

# Configuração do circuit breaker simulado
FIRESTORE_FAILURE_MODE = False  # Altere para True para simular falhas no Firestore


class MockFirestore:
    """
    Simulação do Firestore para testes locais.
    """

    @staticmethod
    def get_collection_data(collection: str) -> list[dict[str, Any]]:
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
    def save_collection_data(collection: str, data: list[dict[str, Any]]) -> bool:
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
    async def get_document(
        collection: str, doc_id: str, tenant_id: str | None = None
    ) -> dict[str, Any] | None:
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
                # Verificar tenant_id se fornecido
                if tenant_id and item.get("tenant_id") != tenant_id:
                    continue
                return item

        return None

    @staticmethod
    async def query_documents(
        collection: str,
        filters: list[tuple] | None = None,
        order_by: list[tuple] | None = None,
        limit: int = 20,
        offset: int = 0,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
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

                    if (
                        op == "=="
                        and item_value != value
                        or op == "!="
                        and item_value == value
                        or op == "<"
                        and (item_value is None or item_value >= value)
                        or op == "<="
                        and (item_value is None or item_value > value)
                        or op == ">"
                        and (item_value is None or item_value <= value)
                        or op == ">="
                        and (item_value is None or item_value < value)
                    ):
                        match = False
                        break

                if match:
                    filtered_items.append(item)

            items = filtered_items

        # Filtrar por tenant_id se fornecido
        if tenant_id:
            items = [item for item in items if item.get("tenant_id") == tenant_id]

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
        collection: str,
        data: dict[str, Any],
        doc_id: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
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

        # Adicionar tenant_id se fornecido
        if tenant_id:
            data["tenant_id"] = tenant_id

        # Adicionar documento
        items.append(data)

        # Salvar dados
        MockFirestore.save_collection_data(collection, items)

        return data

    @staticmethod
    async def update_document(
        collection: str,
        doc_id: str,
        data: dict[str, Any],
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
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
                # Verificar tenant_id se fornecido
                if tenant_id and item.get("tenant_id") != tenant_id:
                    continue

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

    @staticmethod
    async def count_documents(
        collection: str,
        filters: list[tuple] | None = None,
        tenant_id: str | None = None,
    ) -> int:
        """
        Conta documentos no Firestore simulado.
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

                    if (
                        op == "=="
                        and item_value != value
                        or op == "!="
                        and item_value == value
                        or op == "<"
                        and (item_value is None or item_value >= value)
                        or op == "<="
                        and (item_value is None or item_value > value)
                        or op == ">"
                        and (item_value is None or item_value <= value)
                        or op == ">="
                        and (item_value is None or item_value < value)
                    ):
                        match = False
                        break

                if match:
                    filtered_items.append(item)

            items = filtered_items

        # Filtrar por tenant_id se fornecido
        if tenant_id:
            items = [item for item in items if item.get("tenant_id") == tenant_id]

        return len(items)


class MockPostgres:
    """
    Simulação do PostgreSQL para testes locais.
    """

    @staticmethod
    async def get_document(
        table: str, doc_id: str, tenant_id: str | None = None
    ) -> dict[str, Any] | None:
        """
        Obtém um documento do PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.get_document(table, doc_id, tenant_id)

    @staticmethod
    async def query_documents(
        table: str,
        filters: list[tuple] | None = None,
        order_by: list[tuple] | None = None,
        limit: int = 20,
        offset: int = 0,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Consulta documentos no PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.query_documents(
            table, filters, order_by, limit, offset, tenant_id
        )

    @staticmethod
    async def create_document(
        table: str, data: dict[str, Any], tenant_id: str | None = None
    ) -> dict[str, Any]:
        """
        Cria um documento no PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.create_document(
            table, data, data.get("id"), tenant_id
        )

    @staticmethod
    async def update_document(
        table: str,
        doc_id: str,
        data: dict[str, Any],
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Atualiza um documento no PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.update_document(table, doc_id, data, tenant_id)

    @staticmethod
    async def delete_document(table: str, doc_id: str) -> bool:
        """
        Remove um documento do PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.delete_document(table, doc_id)

    @staticmethod
    async def count_documents(
        table: str,
        filters: list[tuple] | None = None,
        tenant_id: str | None = None,
    ) -> int:
        """
        Conta documentos no PostgreSQL simulado.
        """
        # Usar a mesma implementação do Firestore simulado
        return await MockFirestore.count_documents(table, filters, tenant_id)


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


class MockStorageClient:
    """
    Simulação do Firebase Storage para testes locais.
    """

    def __init__(self):
        self.buckets = {}

    def bucket(self, bucket_name="knn-benefits.firebasestorage.app"):
        """Retorna um mock bucket."""
        if bucket_name not in self.buckets:
            self.buckets[bucket_name] = MockBucket(bucket_name)
        return self.buckets[bucket_name]


class MockBucket:
    """
    Simulação de um bucket do Firebase Storage.
    """

    def __init__(self, name):
        self.name = name
        self.blobs = {}

    def blob(self, blob_name):
        """Retorna um mock blob."""
        if blob_name not in self.blobs:
            self.blobs[blob_name] = MockBlob(blob_name, self)
        return self.blobs[blob_name]

    def list_blobs(self, prefix=None):
        """Lista blobs com prefixo opcional."""
        if prefix:
            return [blob for name, blob in self.blobs.items() if name.startswith(prefix)]
        return list(self.blobs.values())


class MockBlob:
    """
    Simulação de um blob do Firebase Storage.
    """

    def __init__(self, name, bucket):
        self.name = name
        self.bucket = bucket
        self.exists_flag = False
        self.content = b""
        self.content_type = "application/octet-stream"

    def exists(self):
        """Verifica se o blob existe."""
        return self.exists_flag

    def upload_from_file(self, file_obj, content_type=None):
        """Simula upload de arquivo."""
        self.content = file_obj.read()
        if content_type:
            self.content_type = content_type
        self.exists_flag = True
        print(f"Mock upload: {self.name} ({len(self.content)} bytes)")

    def upload_from_string(self, data, content_type=None):
        """Simula upload de string."""
        if isinstance(data, str):
            self.content = data.encode()
        else:
            self.content = data
        if content_type:
            self.content_type = content_type
        self.exists_flag = True
        print(f"Mock upload: {self.name} ({len(self.content)} bytes)")

    def delete(self):
        """Simula exclusão do blob."""
        self.exists_flag = False
        self.content = b""
        print(f"Mock delete: {self.name}")

    def make_public(self):
        """Simula tornar o blob público."""
        print(f"Mock make_public: {self.name}")

    @property
    def public_url(self):
        """Retorna URL pública simulada."""
        return f"https://storage.googleapis.com/{self.bucket.name}/{self.name}"


# Instâncias globais
mock_firestore = MockFirestore()
mock_postgres = MockPostgres()
mock_circuit_breaker = MockCircuitBreaker()
mock_storage_client = MockStorageClient()


if __name__ == "__main__":
    print("Módulo de simulação de banco de dados para testes locais.")
    print(
        "Use as classes MockFirestore, MockPostgres e MockCircuitBreaker para testes."
    )
    print(
        "Use a função toggle_firestore_failure_mode() para simular falhas no Firestore."
    )
