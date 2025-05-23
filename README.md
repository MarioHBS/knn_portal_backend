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

```
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
```

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
   ```
   pip install -r requirements.txt
   ```

### Execução Local

Para iniciar o servidor em modo de desenvolvimento:

```
python run_server.py
```

Para executar com dados simulados (sem Firestore/PostgreSQL reais):

```
KNN_TEST_MODE=true python run_server.py
```

### Testes

Para executar todos os testes automatizados:

```
./run_tests.sh
```

Para testes manuais, siga as instruções em `manual_tests.md`.

### Deploy

Para fazer deploy no Google Cloud Run:

```
./deploy_cloudrun.sh
```

## Tokens JWT para Testes

Para facilitar os testes, você pode usar os seguintes tokens JWT:

### Token de Aluno
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50LWlkIiwicm9sZSI6InN0dWRlbnQiLCJleHAiOjE3MTY5OTIwMDAsImlhdCI6MTcxNjkwNTYwMH0.8Uj7hl5vYGnEZQGR5QeQQOdTKB4ZXEfEiqxJxlE5Pjw
```

### Token de Parceiro
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJ0bmVyLWlkIiwicm9sZSI6InBhcnRuZXIiLCJleHAiOjE3MTY5OTIwMDAsImlhdCI6MTcxNjkwNTYwMH0.Hn5Fq5qSVBN5QjuoYd2KBjTIGJJoV9OQh-VzpNqJrSs
```

### Token de Administrador
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbi1pZCIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcxNjk5MjAwMCwiaWF0IjoxNzE2OTA1NjAwfQ.jQyOq0-KnzH0vqBQwKsqzTBGzKqGLYVj9WdAZKbK5Hs
```

## Documentação da API

A documentação completa da API está disponível em:

- Swagger UI: http://localhost:8080/v1/docs
- ReDoc: http://localhost:8080/v1/redoc
- OpenAPI JSON: http://localhost:8080/v1/openapi.json

Além disso, o arquivo `openapi.yaml` contém a especificação completa da API.
