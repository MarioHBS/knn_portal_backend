# Sistema de Banco de Dados Unificado

Este sistema fornece uma interface unificada para operações de banco de dados que funciona com Firestore (primário) e PostgreSQL (fallback), incluindo circuit breaker, tratamento robusto de erros e query builder avançado.

## Arquitetura

### Componentes Principais

1. **UnifiedDatabaseClient** (`unified_client.py`)
   - Interface principal para todas as operações CRUD
   - Integra Firestore e PostgreSQL com circuit breaker
   - Suporte a multi-tenant
   - Tratamento automático de erros

2. **QueryBuilder** (`query_builder.py`)
   - Construtor de queries fluente e intuitivo
   - Suporte a filtros complexos, ordenação e paginação
   - Helpers para buscas comuns (texto, data, etc.)

3. **ErrorHandler** (`error_handler.py`)
   - Sistema robusto de tratamento de erros
   - Retry automático com backoff exponencial
   - Logging detalhado de erros
   - Exceções específicas por tipo de erro

4. **CircuitBreaker** (`circuit_breaker.py`)
   - Fallback automático entre Firestore e PostgreSQL
   - Monitoramento de saúde dos bancos
   - Recuperação automática

## Uso Básico

### Operações CRUD

```python
from src.db.unified_client import unified_client

# Criar documento
usuario = await unified_client.create_document(
    "usuarios", 
    {"nome": "João", "email": "joao@exemplo.com"}, 
    "tenant_123"
)

# Obter documento
usuario = await unified_client.get_document(
    "usuarios", "user_id", "tenant_123"
)

# Atualizar documento
await unified_client.update_document(
    "usuarios", "user_id", {"idade": 30}, "tenant_123"
)

# Deletar documento
await unified_client.delete_document(
    "usuarios", "user_id", "tenant_123"
)
```

### Queries com Filtros

```python
# Query simples
resultado = await unified_client.query_documents(
    collection="usuarios",
    tenant_id="tenant_123",
    filters=[
        ("ativo", "==", True),
        ("idade", ">=", 18)
    ],
    order_by=[("nome", "asc")],
    limit=10
)
```

### QueryBuilder Avançado

```python
from src.db.query_builder import QueryBuilder, SearchHelper

# Query complexa
query = (QueryBuilder("usuarios", "tenant_123")
    .where("ativo", "==", True)
    .where("idade", ">=", 21)
    .order_by("nome", "asc")
    .limit(20)
    .offset(0))

resultado = await query.execute()

# Busca por texto
usuarios = await SearchHelper.search_by_text(
    "usuarios", "nome", "João", "tenant_123"
)

# Busca por range de datas
usuarios_recentes = await SearchHelper.search_by_date_range(
    "usuarios", "created_at", "2024-01-01", "2024-01-31", "tenant_123"
)
```

### Operações em Lote

```python
operacoes = [
    {
        "type": "create",
        "collection": "usuarios",
        "data": {"nome": "Maria", "email": "maria@exemplo.com"}
    },
    {
        "type": "update",
        "collection": "usuarios",
        "doc_id": "user_123",
        "data": {"ultimo_acesso": "2024-01-15"}
    }
]

sucesso = await unified_client.batch_operation(operacoes, "tenant_123")
```

## Tratamento de Erros

O sistema inclui tratamento automático de erros com:

- **Retry automático**: Tentativas automáticas com backoff exponencial
- **Logging detalhado**: Logs estruturados para debugging
- **Exceções específicas**: Diferentes tipos de erro para tratamento adequado
- **Validações**: Validação automática de campos obrigatórios

### Exceções Disponíveis

```python
from src.db.error_handler import (
    DatabaseError,
    ConnectionError,
    ValidationError,
    TimeoutError,
    AuthenticationError
)

try:
    resultado = await unified_client.get_document(...)
except ValidationError as e:
    # Erro de validação de dados
    logger.error(f"Dados inválidos: {e}")
except ConnectionError as e:
    # Erro de conexão
    logger.error(f"Falha na conexão: {e}")
except DatabaseError as e:
    # Erro geral de banco
    logger.error(f"Erro de banco: {e}")
```

## Multi-Tenant

Todas as operações são multi-tenant por padrão:

- Cada operação requer um `tenant_id`
- Isolamento automático de dados por tenant
- Validação de acesso por tenant

## Circuit Breaker

O sistema monitora automaticamente a saúde dos bancos:

- **Firestore como primário**: Tentativa inicial sempre no Firestore
- **PostgreSQL como fallback**: Usado quando Firestore falha
- **Recuperação automática**: Volta ao Firestore quando disponível
- **Monitoramento contínuo**: Verifica saúde dos bancos periodicamente

## Configuração

### Variáveis de Ambiente

```bash
# Firestore
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
FIRESTORE_PROJECT_ID=your-project-id

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Error Handler
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
```

## Exemplos Completos

Veja o arquivo `examples/usage_example.py` para exemplos completos de uso incluindo:

- Operações CRUD básicas
- Queries avançadas com filtros
- Uso do QueryBuilder
- Operações em lote
- Paginação de resultados
- Tratamento de erros

## Estrutura de Arquivos

```
src/db/
├── unified_client.py      # Cliente principal unificado
├── query_builder.py       # Construtor de queries
├── error_handler.py       # Sistema de tratamento de erros
├── circuit_breaker.py     # Circuit breaker para fallback
├── firestore.py          # Cliente Firestore
├── postgres.py           # Cliente PostgreSQL
├── examples/
│   └── usage_example.py  # Exemplos de uso
└── README.md             # Esta documentação
```

## Melhores Práticas

1. **Sempre use tenant_id**: Garante isolamento de dados
2. **Trate exceções específicas**: Use as exceções apropriadas para cada caso
3. **Use paginação**: Para consultas que podem retornar muitos resultados
4. **Monitore logs**: O sistema gera logs detalhados para debugging
5. **Teste fallback**: Verifique se o PostgreSQL está configurado corretamente
6. **Use operações em lote**: Para múltiplas operações simultâneas
7. **Valide dados**: O sistema valida automaticamente, mas validação adicional é recomendada

## Performance

- **Cache automático**: Resultados são cacheados quando possível
- **Conexões persistentes**: Reutilização de conexões de banco
- **Queries otimizadas**: Índices apropriados são recomendados
- **Paginação eficiente**: Use limit/offset para grandes datasets
- **Operações assíncronas**: Todas as operações são não-bloqueantes

## Monitoramento

O sistema gera métricas e logs para:

- Tempo de resposta das operações
- Taxa de sucesso/falha por banco
- Uso do circuit breaker
- Erros e exceções
- Performance de queries

Use essas informações para otimizar e monitorar a saúde do sistema.