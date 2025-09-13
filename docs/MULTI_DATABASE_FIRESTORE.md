# Múltiplos Bancos Firestore

Este documento descreve a implementação de suporte a múltiplos bancos de dados Firestore no projeto.

## Configuração

### Variáveis de Ambiente

As seguintes variáveis devem ser configuradas no arquivo `.env`:

```env
# Projeto principal do Firestore
FIRESTORE_PROJECT=knn-benefits

# Lista de bancos disponíveis (formato JSON)
FIRESTORE_DATABASES=["(default)","knn-benefits"]

# Índice do banco principal (0-based)
FIRESTORE_DATABASE=0

# Configurações de autenticação (opcionais)
# GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account-key.json
# FIRESTORE_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
```

### Explicação das Variáveis

- **FIRESTORE_PROJECT**: Nome do projeto Firebase/Firestore
- **FIRESTORE_DATABASES**: Array JSON com os nomes dos bancos disponíveis
- **FIRESTORE_DATABASE**: Índice (começando em 0) do banco que será usado como principal
- **GOOGLE_APPLICATION_CREDENTIALS**: Caminho para arquivo de credenciais do service account (opcional)
- **FIRESTORE_SERVICE_ACCOUNT_KEY**: JSON string com credenciais do service account (opcional)

### Autenticação

O sistema suporta múltiplas formas de autenticação, em ordem de prioridade:

1. **Service Account Key (JSON string)**: Via variável `FIRESTORE_SERVICE_ACCOUNT_KEY`
2. **Service Account File**: Via variável `GOOGLE_APPLICATION_CREDENTIALS`
3. **Application Default Credentials (ADC)**: Credenciais padrão do ambiente

#### Exemplo com Service Account Key:

```env
FIRESTORE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"knn-benefits",...}'
```

#### Exemplo com Arquivo de Credenciais:

```env
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account-key.json
```

#### Usando ADC (Recomendado para desenvolvimento):

```bash
# Configure as credenciais padrão
gcloud auth application-default login
```

## Funcionalidades Implementadas

### 1. Inicialização Automática

O sistema inicializa automaticamente conexões com todos os bancos configurados:

```python
from src.db.firestore import db, databases

# db = banco principal configurado
# databases = dicionário com todas as conexões
```

### 2. Acesso ao Banco Principal

```python
from src.db.firestore import db

# Usar o banco principal diretamente
if db:
    collection = db.collection('users')
    doc = collection.document('user_id').get()
```

### 3. Acesso a Bancos Específicos

```python
from src.db.firestore import get_database

# Acessar um banco específico
benefits_db = get_database('knn-benefits')
default_db = get_database('(default)')

# Se não especificar, retorna o banco principal
main_db = get_database()  # mesmo que usar 'db' diretamente
```

### 4. Utilitários

```python
from src.db.firestore import (
    list_available_databases,
    get_current_database_name
)

# Listar todos os bancos disponíveis
available = list_available_databases()
print(f"Bancos disponíveis: {available}")

# Obter nome do banco principal
current = get_current_database_name()
print(f"Banco principal: {current}")
```

## Exemplos de Uso

### Exemplo 1: Operações Multi-Tenant

```python
from src.db.firestore import get_database

def get_user_data(user_id: str, tenant: str):
    """Busca dados do usuário no banco apropriado."""

    if tenant == 'benefits':
        db = get_database('knn-benefits')
    else:
        db = get_database('(default)')

    return db.collection('users').document(user_id).get()
```

### Exemplo 2: Migração de Dados

```python
from src.db.firestore import get_database

def migrate_data_between_databases():
    """Migra dados entre bancos."""

    source_db = get_database('(default)')
    target_db = get_database('knn-benefits')

    # Ler dados do banco origem
    docs = source_db.collection('data').stream()

    # Escrever no banco destino
    for doc in docs:
        target_db.collection('data').document(doc.id).set(doc.to_dict())
```

### Exemplo 3: Operações Paralelas

```python
import asyncio
from src.db.firestore import get_database, list_available_databases

async def query_all_databases(collection_name: str):
    """Consulta uma coleção em todos os bancos."""

    results = {}

    for db_name in list_available_databases():
        db = get_database(db_name)
        docs = db.collection(collection_name).limit(10).stream()
        results[db_name] = [doc.to_dict() for doc in docs]

    return results
```

## Configurações Avançadas

### Alterando o Banco Principal

Para alterar qual banco é usado como principal, modifique a variável `FIRESTORE_DATABASE`:

```env
# Para usar o segundo banco da lista como principal
FIRESTORE_DATABASE=1
```

### Adicionando Novos Bancos

Para adicionar um novo banco, atualize a lista `FIRESTORE_DATABASES`:

```env
# Adicionar um terceiro banco
FIRESTORE_DATABASES=["(default)","knn-benefits","knn-analytics"]
```

## Tratamento de Erros

O sistema inclui tratamento robusto de erros:

```python
from src.db.firestore import get_database
from src.utils import logger

def safe_database_operation(database_name: str):
    """Operação segura com tratamento de erros."""

    db = get_database(database_name)

    if not db:
        logger.error(f"Banco {database_name} não disponível")
        return None

    try:
        # Sua operação aqui
        result = db.collection('test').limit(1).get()
        return result
    except Exception as e:
        logger.error(f"Erro ao acessar {database_name}: {e}")
        return None
```

## Logs e Monitoramento

O sistema gera logs detalhados sobre:

- Inicialização de conexões
- Seleção do banco principal
- Erros de conectividade
- Operações em bancos específicos

Exemplo de logs:

```text
INFO: Conexão estabelecida com banco: (default)
INFO: Conexão estabelecida com banco: knn-benefits
INFO: Banco principal definido: (default)
WARNING: Banco analytics não encontrado, usando banco principal
```

## Script de Teste

Use o script de exemplo para testar a funcionalidade:

```bash
python scripts/examples/multi_database_example.py
```

Este script demonstra:

- Listagem de bancos disponíveis
- Acesso ao banco principal
- Operações em bancos específicos
- Testes de conectividade
- Alternância entre bancos

## Migração de Código Existente

### Antes (código antigo)

```python
from src.config import FB_PROJECT_ID
from src.db.firestore import db

# Código usava FB_PROJECT_ID
project = FB_PROJECT_ID
```

### Depois (código atualizado)

```python
from src.config import FIRESTORE_PROJECT
from src.db.firestore import db, get_database

# Agora usa FIRESTORE_PROJECT
project = FIRESTORE_PROJECT

# Pode acessar bancos específicos
specific_db = get_database('knn-benefits')
```

## Considerações de Performance

1. **Conexões Reutilizadas**: As conexões são inicializadas uma vez e reutilizadas
2. **Lazy Loading**: Bancos são conectados apenas se estiverem na lista configurada
3. **Cache de Clientes**: Os clientes Firestore são armazenados em cache
4. **Fallback Inteligente**: Se um banco não estiver disponível, usa o principal

## Troubleshooting

### Problema: Banco não encontrado

```text
WARNING: Banco analytics não encontrado, usando banco principal
```

**Solução**: Verifique se o banco está listado em `FIRESTORE_DATABASES`

### Problema: Erro de inicialização

```text
ERROR: Erro ao conectar com banco knn-benefits: [Firestore] Database 'knn-benefits' does not exist
```

**Solução**: Verifique se o banco existe no projeto Firebase

### Problema: Credenciais

```text
ERROR: Erro ao inicializar Firebase com credenciais padrão
```

**Solução**: Configure as credenciais do Firebase ou use o emulador

## Migração para google-cloud-firestore

### Mudanças na Implementação

A partir da versão atual, o sistema migrou do `firebase-admin` para `google-cloud-firestore` para melhor suporte a múltiplos bancos:

#### Antes (firebase-admin)

```python
import firebase_admin
from firebase_admin import firestore

app = firebase_admin.initialize_app()
db = firestore.client(app)
```

#### Depois (google-cloud-firestore)

```python
from google.cloud import firestore
from google.oauth2 import service_account

# Com credenciais específicas
credentials = service_account.Credentials.from_service_account_info(key_info)
client = firestore.Client(project=project_id, credentials=credentials, database=database_id)

# Com credenciais padrão
client = firestore.Client(project=project_id, database=database_id)
```

### Vantagens da Migração

1. **Suporte Nativo a Múltiplos Bancos**: Cada cliente pode conectar a um banco específico
2. **Melhor Controle de Credenciais**: Suporte a diferentes métodos de autenticação
3. **Performance Otimizada**: Conexões diretas sem overhead do firebase-admin
4. **Flexibilidade**: Maior controle sobre configurações de cliente

### Dependências Atualizadas

```txt
# requirements.txt
google-cloud-firestore==2.19.0
# firebase-admin removido (não mais necessário para Firestore)
```

## Compatibilidade

Esta implementação é compatível com:

- google-cloud-firestore v2.19.0+
- Python 3.8+
- Firestore em modo nativo
- Emulador Firestore (desenvolvimento)
- Application Default Credentials (ADC)
- Service Account Keys (arquivo ou JSON string)

## Próximos Passos

1. Implementar balanceamento de carga entre bancos
2. Adicionar métricas de performance por banco
3. Implementar failover automático
4. Adicionar suporte a transações cross-database
