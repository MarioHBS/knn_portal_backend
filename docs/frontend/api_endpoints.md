# API Endpoints - Portal de Benefícios KNN

## Visão Geral

Esta documentação descreve os endpoints da API que o Frontend deve consumir. Os IDs são gerados automaticamente pelo Backend.

## Base URL

```
Desenvolvimento: http://localhost:8000/api/v1
Homologação: https://knn-portal-hml.cloudrun.app/api/v1
Produção: https://knn-portal.cloudrun.app/api/v1
```

## Headers Obrigatórios

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
X-Tenant-ID: <school_id>
```

## Endpoints

### 1. Estudantes

#### Criar Estudante
```http
POST /students
```

**Request Body:**
```json
{
  "nome": "João Silva Santos",
  "email": "joao.santos@email.com",
  "telefone": "(11) 99999-9999",
  "cep": "01234-567",
  "curso": "Engenharia de Software",
  "data_nascimento": "2000-05-15",
  "nome_responsavel": "Maria Silva Santos"
}
```

**Response (201):**
```json
{
  "id": "STD_J6S7S899_K1",
  "nome": "João Silva Santos",
  "email": "joao.santos@email.com",
  "telefone": "(11) 99999-9999",
  "cep": "01234-567",
  "curso": "Engenharia de Software",
  "data_nascimento": "2000-05-15",
  "nome_responsavel": "Maria Silva Santos",
  "created_at": "2025-01-21T10:30:00Z",
  "updated_at": "2025-01-21T10:30:00Z"
}
```

#### Listar Estudantes
```http
GET /students?page=1&limit=20
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "STD_J6S7S899_K1",
      "nome": "João Silva Santos",
      "email": "joao.santos@email.com",
      "curso": "Engenharia de Software"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

#### Buscar Estudante por ID
```http
GET /students/{id}
```

**Response (200):**
```json
{
  "id": "STD_J6S7S899_K1",
  "nome": "João Silva Santos",
  "email": "joao.santos@email.com",
  "telefone": "(11) 99999-9999",
  "cep": "01234-567",
  "curso": "Engenharia de Software",
  "data_nascimento": "2000-05-15",
  "nome_responsavel": "Maria Silva Santos",
  "created_at": "2025-01-21T10:30:00Z",
  "updated_at": "2025-01-21T10:30:00Z"
}
```

### 2. Funcionários

#### Criar Funcionário
```http
POST /employees
```

**Request Body:**
```json
{
  "nome": "Carlos Eduardo Silva",
  "email": "carlos.silva@escola.edu.br",
  "telefone": "(11) 88888-8888",
  "cep": "12345-678",
  "cargo": "Professor",
  "data_nascimento": "1985-03-20"
}
```

**Response (201):**
```json
{
  "id": "EMP_C2E22555_PR",
  "nome": "Carlos Eduardo Silva",
  "email": "carlos.silva@escola.edu.br",
  "telefone": "(11) 88888-8888",
  "cep": "12345-678",
  "cargo": "Professor",
  "data_nascimento": "1985-03-20",
  "created_at": "2025-01-21T10:30:00Z",
  "updated_at": "2025-01-21T10:30:00Z"
}
```

#### Listar Funcionários
```http
GET /employees?page=1&limit=20
```

### 3. Parceiros

#### Criar Parceiro
```http
POST /partners
```

**Request Body:**
```json
{
  "nome_comercial": "Tech Solutions LTDA",
  "cnpj": "12.345.678/0001-90",
  "categoria": "Tecnologia",
  "email": "contato@techsolutions.com.br",
  "telefone": "(11) 77777-7777"
}
```

**Response (201):**
```json
{
  "id": "PTN_T4S5678_TEC",
  "nome_comercial": "Tech Solutions LTDA",
  "cnpj": "12.345.678/0001-90",
  "categoria": "Tecnologia",
  "email": "contato@techsolutions.com.br",
  "telefone": "(11) 77777-7777",
  "created_at": "2025-01-21T10:30:00Z",
  "updated_at": "2025-01-21T10:30:00Z"
}
```

#### Listar Parceiros
```http
GET /partners?page=1&limit=20
```

## Códigos de Status HTTP

| Código | Descrição |
|--------|----------|
| 200 | Sucesso - Dados retornados |
| 201 | Criado - Recurso criado com sucesso |
| 400 | Erro de validação - Dados inválidos |
| 401 | Não autorizado - Token inválido |
| 403 | Proibido - Sem permissão |
| 404 | Não encontrado - Recurso não existe |
| 422 | Erro de processamento - Dados não processáveis |
| 429 | Muitas requisições - Rate limit excedido |
| 500 | Erro interno do servidor |

## Exemplos de Respostas de Erro

### Erro de Validação (400)
```json
{
  "error": "Validation Error",
  "message": "Dados inválidos fornecidos",
  "details": [
    {
      "field": "email",
      "message": "Formato de email inválido"
    },
    {
      "field": "cep",
      "message": "CEP deve seguir o formato XXXXX-XXX"
    }
  ]
}
```

### Erro de Autorização (401)
```json
{
  "error": "Unauthorized",
  "message": "Token JWT inválido ou expirado"
}
```

### Rate Limit (429)
```json
{
  "error": "Rate Limit Exceeded",
  "message": "Muitas requisições. Tente novamente em 60 segundos",
  "retry_after": 60
}
```

## Validações de Entrada

### Campos Obrigatórios

**Estudantes:**
- `nome` (string, min: 2, max: 100)
- `cep` (string, formato: XXXXX-XXX)
- `curso` (string, deve existir na lista de cursos)
- `data_nascimento` (date, formato: YYYY-MM-DD)

**Funcionários:**
- `nome` (string, min: 2, max: 100)
- `cep` (string, formato: XXXXX-XXX)
- `cargo` (string, deve existir na lista de cargos)
- `data_nascimento` (date, formato: YYYY-MM-DD)

**Parceiros:**
- `nome_comercial` (string, min: 2, max: 100)
- `cnpj` (string, formato: XX.XXX.XXX/XXXX-XX)
- `categoria` (string, deve existir na lista de categorias)

### Campos Opcionais
- `email` (string, formato válido quando preenchido)
- `telefone` (string, formato brasileiro quando preenchido)
- `nome_responsavel` (obrigatório para menores de idade)

## Endpoints Utilitários

### GET /utils/courses
Busca a lista de cursos disponíveis.

**URL**: `{BASE_URL}/utils/courses`

**Método**: GET

**Headers obrigatórios**:
```
Content-Type: application/json
Authorization: Bearer {token}
```

**Resposta de sucesso (200)**:
```json
[
  "KIDS 1",
  "KIDS 2",
  "KIDS 3",
  "SEEDS 1",
  "SEEDS 2",
  "SEEDS 3",
  "TEENS 1",
  "TEENS 2",
  "TEENS 3",
  "TWEENS 1",
  "TWEENS 2",
  "TWEENS 3",
  "KEEP_TALKING 1",
  "KEEP_TALKING 2",
  "KEEP_TALKING 3",
  "ADVANCED 1",
  "ADVANCED 2",
  "KINDER"
]
```

### GET /utils/course-codes
Busca o mapeamento completo de cursos para códigos.

**URL**: `{BASE_URL}/utils/course-codes`

**Método**: GET

**Headers obrigatórios**:
```
Content-Type: application/json
Authorization: Bearer {token}
```

**Resposta de sucesso (200)**:
```json
{
  "KIDS 1": "K1",
  "KIDS 2": "K2",
  "KIDS 3": "K3",
  "SEEDS 1": "S1",
  "SEEDS 2": "S2",
  "SEEDS 3": "S3",
  "TEENS 1": "T1",
  "TEENS 2": "T2",
  "TEENS 3": "T3",
  "TWEENS 1": "TW1",
  "TWEENS 2": "TW2",
  "TWEENS 3": "TW3",
  "KEEP_TALKING 1": "KT1",
  "KEEP_TALKING 2": "KT2",
  "KEEP_TALKING 3": "KT3",
  "ADVANCED 1": "A1",
  "ADVANCED 2": "A2",
  "KINDER": "KD"
}
```

## Rate Limiting

- **Limite:** 100 requisições por minuto por IP
- **Headers de resposta:**
  - `X-RateLimit-Limit`: Limite total
  - `X-RateLimit-Remaining`: Requisições restantes
  - `X-RateLimit-Reset`: Timestamp do reset

## Paginação

**Parâmetros de query:**
- `page`: Número da página (padrão: 1)
- `limit`: Itens por página (padrão: 20, máximo: 100)

**Resposta:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

## Filtros e Busca

### Busca por texto
```http
GET /students?search=joão
GET /employees?search=carlos
GET /partners?search=tech
```

### Filtros específicos
```http
GET /students?curso=Engenharia
GET /employees?cargo=Professor
GET /partners?categoria=Tecnologia
```

## Observações Importantes

1. **IDs são gerados automaticamente** pelo Backend - não envie no request
2. **Todos os endpoints requerem autenticação** via JWT
3. **Use o header X-Tenant-ID** para multi-tenancy
4. **Respeite os rate limits** para evitar bloqueios
5. **Valide dados no Frontend** antes de enviar para a API
6. **Trate todos os códigos de erro** adequadamente
7. **Use HTTPS** em produção