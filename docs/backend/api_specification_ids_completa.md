# Especificação da API - Sistema de IDs Personalizados

## Endpoints Principais

### 1. Estudantes (Students)

#### POST /api/students
Cria um novo estudante com ID personalizado gerado automaticamente.

**Request Body:**
```json
{
  "nome_aluno": "João Silva Santos",
  "curso": "KIDS 1",
  "cep": "12345-678",
  "celular": "(11) 99999-9999",
  "email": "joao@email.com",
  "tenant_id": "escola_abc",
  "cpf_hash": "hash_do_cpf"
}
```

**Response (201 Created):**
```json
{
  "id": "STD_J6S7S899_K1",
  "nome_aluno": "João Silva Santos",
  "curso": "KIDS 1",
  "cep": "12345-678",
  "celular": "(11) 99999-9999",
  "email": "joao@email.com",
  "tenant_id": "escola_abc",
  "cpf_hash": "hash_do_cpf",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### GET /api/students
Lista todos os estudantes.

**Query Parameters:**
- `limit` (opcional): Número máximo de resultados (padrão: 50)
- `offset` (opcional): Número de registros para pular (padrão: 0)
- `curso` (opcional): Filtrar por curso específico
- `search` (opcional): Buscar por nome

**Response (200 OK):**
```json
{
  "students": [
    {
      "id": "STD_J6S7S899_K1",
      "nome_aluno": "João Silva Santos",
      "curso": "KIDS 1",
      "email": "joao@email.com",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "STD_M1S23888_T2",
      "nome_aluno": "Maria da Silva",
      "curso": "TEENS 2",
      "email": "maria@escola.com",
      "created_at": "2024-01-15T11:00:00Z"
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

#### GET /api/students/{id}
Obter detalhes de um estudante específico.

**Response (200 OK):**
```json
{
  "id": "STD_J6S7S899_K1",
  "nome_aluno": "João Silva Santos",
  "curso": "KIDS 1",
  "cep": "12345-678",
  "celular": "(11) 99999-9999",
  "email": "joao@email.com",
  "tenant_id": "escola_abc",
  "cpf_hash": "hash_do_cpf",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 2. Funcionários (Employees)

#### POST /api/employees
Cria um novo funcionário com ID personalizado.

**Request Body:**
```json
{
  "name": "Carlos Eduardo Silva",
  "department": "PROFESSOR",
  "cep": "11111-222",
  "telefone": "(11) 55555-5555",
  "email": "carlos@escola.com",
  "tenant_id": "escola_abc"
}
```

**Response (201 Created):**
```json
{
  "id": "EMP_C2E22555_PR",
  "name": "Carlos Eduardo Silva",
  "department": "PROFESSOR",
  "cep": "11111-222",
  "telefone": "(11) 55555-5555",
  "email": "carlos@escola.com",
  "tenant_id": "escola_abc",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### GET /api/employees
Lista todos os funcionários.

**Response (200 OK):**
```json
{
  "employees": [
    {
      "id": "EMP_C2E22555_PR",
      "name": "Carlos Eduardo Silva",
      "department": "PROFESSOR",
      "email": "carlos@escola.com",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### 3. Parceiros (Partners)

#### POST /api/partners
Cria um novo parceiro com ID personalizado.

**Request Body:**
```json
{
  "trade_name": "Tech Solutions Ltda",
  "category": "TECNOLOGIA",
  "cnpj": "12.345.678/0001-90",
  "tenant_id": "escola_abc"
}
```

**Response (201 Created):**
```json
{
  "id": "PTN_T4S5678_TEC",
  "trade_name": "Tech Solutions Ltda",
  "category": "TECNOLOGIA",
  "cnpj": "12.345.678/0001-90",
  "tenant_id": "escola_abc",
  "cnpj_hash": "hash_do_cnpj",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Códigos de Status HTTP

### Sucesso
- `200 OK`: Operação realizada com sucesso
- `201 Created`: Recurso criado com sucesso
- `204 No Content`: Operação realizada sem conteúdo de retorno

### Erros do Cliente
- `400 Bad Request`: Dados inválidos ou malformados
- `401 Unauthorized`: Token de autenticação inválido ou ausente
- `403 Forbidden`: Acesso negado para o recurso
- `404 Not Found`: Recurso não encontrado
- `409 Conflict`: Conflito com estado atual do recurso
- `422 Unprocessable Entity`: Dados válidos mas com regras de negócio violadas

### Erros do Servidor
- `500 Internal Server Error`: Erro interno do servidor
- `503 Service Unavailable`: Serviço temporariamente indisponível

## Exemplos de Respostas de Erro

### Erro de Validação (400 Bad Request)
```json
{
  "error": "Validation Error",
  "message": "Dados de entrada inválidos",
  "details": [
    {
      "field": "nome_aluno",
      "message": "Nome do aluno é obrigatório"
    },
    {
      "field": "curso",
      "message": "Curso deve ser um dos valores válidos"
    },
    {
      "field": "cep",
      "message": "CEP deve estar no formato XXXXX-XXX"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Erro de Autenticação (401 Unauthorized)
```json
{
  "error": "Authentication Error",
  "message": "Token de autenticação inválido ou expirado",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Recurso Não Encontrado (404 Not Found)
```json
{
  "error": "Not Found",
  "message": "Estudante com ID 'STD_INVALID123' não encontrado",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Erro Interno (500 Internal Server Error)
```json
{
  "error": "Internal Server Error",
  "message": "Erro interno do servidor. Tente novamente mais tarde.",
  "request_id": "req_123456789",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Headers Obrigatórios

### Autenticação
```
Authorization: Bearer <jwt_token>
```

### Content-Type (para requisições POST/PUT)
```
Content-Type: application/json
```

### Tenant (Multi-tenancy)
```
X-Tenant-ID: escola_abc
```

## Padrões de ID por Entidade

### Estudantes
- **Formato**: `STD_<codigo_intercalado>_<sufixo_curso>`
- **Exemplo**: `STD_J6S7S899_K1`
- **Sufixos Válidos**: K1, K2, K3, T1, T2, T3, A1, A2, A3, CV, BZ, OT

### Funcionários
- **Formato**: `EMP_<codigo_intercalado>_<sufixo_cargo>`
- **Exemplo**: `EMP_C2E22555_PR`
- **Sufixos Válidos**: PR, CDA, AF, CO, OT

### Parceiros
- **Formato**: `PTN_<codigo_intercalado>_<sufixo_categoria>`
- **Exemplo**: `PTN_T4S5678_TEC`
- **Sufixos Válidos**: TEC, SAU, EDU, ALI, VAR, SER, OT

## Validações de Entrada

### Campos Obrigatórios

#### Estudantes
- `nome_aluno`: String, não vazio
- `curso`: String, deve ser um dos cursos válidos
- `tenant_id`: String, não vazio

#### Funcionários
- `name`: String, não vazio
- `department`: String, deve ser um dos departamentos válidos
- `tenant_id`: String, não vazio

#### Parceiros
- `trade_name`: String, não vazio
- `category`: String, deve ser uma das categorias válidas
- `tenant_id`: String, não vazio

### Formatos Específicos

#### CEP
- **Formato**: `XXXXX-XXX` (5 dígitos, hífen, 3 dígitos)
- **Exemplo**: `12345-678`
- **Regex**: `^\d{5}-\d{3}$`

#### Telefone/Celular
- **Formato**: `(XX) XXXXX-XXXX` ou `(XX) XXXX-XXXX`
- **Exemplo**: `(11) 99999-9999`
- **Regex**: `^\(\d{2}\)\s\d{4,5}-\d{4}$`

#### CNPJ
- **Formato**: `XX.XXX.XXX/XXXX-XX`
- **Exemplo**: `12.345.678/0001-90`
- **Regex**: `^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$`

#### Email
- **Formato**: Padrão RFC 5322
- **Exemplo**: `usuario@dominio.com`
- **Regex**: `^[^\s@]+@[^\s@]+\.[^\s@]+$`

## Rate Limiting

- **Limite**: 100 requisições por minuto por IP
- **Headers de Resposta**:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1642248600
  ```

## Paginação

### Parâmetros de Query
- `limit`: Número máximo de itens por página (padrão: 50, máximo: 100)
- `offset`: Número de itens para pular (padrão: 0)

### Resposta com Paginação
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "has_next": true,
    "has_previous": false,
    "next_offset": 50,
    "previous_offset": null
  }
}
```

## Versionamento da API

- **Versão Atual**: v1
- **Base URL**: `https://api.escola.com/v1`
- **Header de Versão**: `Accept: application/vnd.api+json;version=1`

## Ambientes

### Desenvolvimento
- **URL**: `https://dev-api.escola.com/v1`
- **Autenticação**: Token de desenvolvimento

### Homologação
- **URL**: `https://staging-api.escola.com/v1`
- **Autenticação**: Token de homologação

### Produção
- **URL**: `https://api.escola.com/v1`
- **Autenticação**: Token de produção

## Monitoramento e Logs

### Request ID
Todas as respostas incluem um header `X-Request-ID` para rastreamento:
```
X-Request-ID: req_1234567890abcdef
```

### Logs de Auditoria
Todas as operações de criação, atualização e exclusão são registradas com:
- Timestamp
- Usuário responsável
- Ação realizada
- Dados alterados
- Request ID

Esta especificação fornece todos os detalhes técnicos necessários para integração completa com o sistema de IDs personalizados.