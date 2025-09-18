# Portal de Benefícios KNN - Documentação

## Visão Geral

O Portal de Benefícios KNN é uma API REST desenvolvida com FastAPI para gerenciar benefícios oferecidos a alunos da KNN Idiomas por parceiros comerciais. O sistema permite que alunos visualizem parceiros e promoções, gerem códigos de validação, e que parceiros resgatem esses códigos para oferecer benefícios.

## Arquitetura

- **Backend**: FastAPI + asyncpg em contêiner
- **Banco de Dados**:
  - Primário: Firestore multi-região
  - Contingência: PostgreSQL (espelho diário via Pub/Sub)
- **Autenticação**: JWT Bearer obrigatório em todas as rotas
- **Resiliência**: Circuit-breaker para fallback entre Firestore e PostgreSQL
- **Segurança**: CPF nunca armazenado em texto claro, sempre em hash SHA-256

## Estrutura do Projeto

```text
portal-knn/
├── src/                      # Código-fonte principal
│   ├── api/                  # Endpoints da API
│   │   ├── student.py        # Endpoints para alunos
│   │   ├── partner.py        # Endpoints para parceiros
│   │   ├── admin.py          # Endpoints para administradores
│   │   └── __init__.py       # Inicialização do router
│   ├── db/                   # Camada de acesso a dados
│   │   ├── firestore.py      # Cliente Firestore
│   │   ├── postgres.py       # Cliente PostgreSQL
│   │   ├── circuit_breaker.py # Implementação do circuit breaker
│   │   ├── mock_db.py        # Simulação de banco para testes
│   │   └── __init__.py       # Inicialização do módulo de dados
│   ├── models/               # Modelos de dados
│   │   └── __init__.py       # Definições Pydantic
│   ├── utils/                # Utilitários
│   │   ├── logging.py        # Configuração de logs
│   │   ├── rate_limit.py     # Limitação de requisições
│   │   ├── security.py       # Funções de segurança
│   │   ├── business_rules.py # Regras de negócio
│   │   └── __init__.py       # Inicialização de utilitários
│   ├── auth.py               # Autenticação e autorização
│   ├── config.py             # Configurações do sistema
│   └── main.py               # Ponto de entrada da aplicação
├── tests/                    # Testes automatizados
│   └── test_api.py           # Testes dos endpoints
├── Dockerfile                # Configuração do contêiner
├── requirements.txt          # Dependências Python
├── openapi.yaml              # Documentação OpenAPI
├── deploy_cloudrun.sh        # Script de deploy no Cloud Run
├── run_server.py             # Script para iniciar servidor local
├── test_endpoints.py         # Script para testar endpoints
├── generate_test_data.py     # Geração de dados para testes
├── run_tests.sh              # Script para executar testes
├── seed_dev.py               # Script para criar dados iniciais
├── manual_tests.md           # Documentação de testes manuais
└── README.md                 # Documentação principal
`$language

## Perfis de Usuário

O sistema possui três perfis de usuário:

1. **Aluno (student)**: Visualiza parceiros, gera códigos de validação, gerencia favoritos
2. **Parceiro (partner)**: Resgata códigos, gerencia promoções, visualiza relatórios
3. **Administrador (admin)**: Gerencia alunos, parceiros, promoções e visualiza métricas

## Regras de Negócio Principais

- Códigos de validação são numéricos de 6 dígitos e expiram em 3 minutos
- Códigos só podem ser usados uma vez
- Alunos só podem gerar códigos se estiverem com matrícula ativa
- Parceiros têm limite de 5 resgates por minuto por IP
- CPF é validado e armazenado apenas como hash

## Resiliência e Segurança

- Circuit-breaker: após 3 falhas consecutivas no Firestore, o sistema usa apenas PostgreSQL
- Logs estruturados com mascaramento de CPF
- CORS restrito aos domínios permitidos
- Verificação de assinatura JWT via JWKS

## Como Executar

### Requisitos

- Python 3.11+
- Docker (opcional, para contêiner)

### Instalação

1. Clone o repositório
2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   - Copie o arquivo `.env.example` para `.env` e ajuste as configurações conforme necessário:

     ```bash
     cp .env.example .env
     ```

   - As principais variáveis são:
     - `KNN_USE_TEST_DATABASE`: Define se deve usar dados simulados (true/false)
     - `DEBUG`: Ativa logs detalhados (true/false)
     - `ENVIRONMENT`: Ambiente de execução (development/staging/production)
     - `PORT`: Porta do servidor (padrão: 8080)

### Execução Local

Para iniciar o servidor em modo de desenvolvimento:

```bash
python scripts/run_server.py
`$language

Para executar com dados simulados (sem Firestore/PostgreSQL reais):

```bash

# Opção 1: Definir variável de ambiente

KNN_USE_TEST_DATABASE=true python scripts/run_server.py

# Opção 2: Editar o arquivo .env e definir KNN_USE_TEST_DATABASE=true

python scripts/run_server.py
`$language

### Variáveis de Ambiente

O projeto suporta as seguintes variáveis de ambiente (definidas no arquivo `.env`):

- **KNN_USE_TEST_DATABASE**: Modo de teste com dados simulados (true/false)
- **DEBUG**: Ativa logs detalhados (true/false)
- **ENVIRONMENT**: Ambiente de execução (development/staging/production)
- **PORT**: Porta do servidor (padrão: 8080)
- **FIRESTORE_PROJECT**: ID do projeto Firestore
- **POSTGRES_CONNECTION_STRING**: String de conexão PostgreSQL
- **CNPJ_HASH_SALT**: Salt para hash de CNPJ
- **CPF_HASH_SALT**: Salt para hash de CPF
- **JWKS_URL**: URL do JWKS para validação JWT
- **MODE**: Modo de operação (normal/degraded)

### Testes

Para executar todos os testes automatizados (incluindo linting com Ruff):

```bash
./run_tests.sh
`$language

Para executar apenas o linting:

```bash
ruff check src/
ruff format src/
`$language

Para testes manuais, siga as instruções em `manual_tests.md`.

### Deploy

Para fazer deploy no Google Cloud Run:

```bash
./deploy_cloudrun.sh
`$language

## Tokens JWT para Testes

Para facilitar os testes, você pode usar os seguintes tokens JWT:

### Token de Aluno

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50LWlkIiwicm9sZSI6InN0dWRlbnQiLCJleHAiOjE3MTY5OTIwMDAsImlhdCI6MTcxNjkwNTYwMH0.8Uj7hl5vYGnEZQGR5QeQQOdTKB4ZXEfEiqxJxlE5Pjw
`$language

### Token de Parceiro

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJ0bmVyLWlkIiwicm9sZSI6InBhcnRuZXIiLCJleHAiOjE3MTY5OTIwMDAsImlhdCI6MTcxNjkwNTYwMH0.Hn5Fq5qSVBN5QjuoYd2KBjTIGJJoV9OQh-VzpNqJrSs
`$language

### Token de Administrador

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbi1pZCIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcxNjk5MjAwMCwiaWF0IjoxNzE2OTA1NjAwfQ.jQyOq0-KnzH0vqBQwKsqzTBGzKqGLYVj9WdAZKbK5Hs
`$language

## Documentação da API

A documentação completa da API está disponível em:

- Swagger UI: [http://localhost:8080/v1/docs](http://localhost:8080/v1/docs)
- ReDoc: [http://localhost:8080/v1/redoc](http://localhost:8080/v1/redoc)
- OpenAPI JSON: [http://localhost:8080/v1/openapi.json](http://localhost:8080/v1/openapi.json)

Além disso, o arquivo `openapi.yaml` contém a especificação completa da API.
