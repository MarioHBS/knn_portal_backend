# Análise de Requisitos - Portal de Benefícios KNN

## 1. Stack Tecnológica

- **Backend**: FastAPI com asyncpg
- **Implantação**: Contêiner com deploy automático no Cloud Run
- **Armazenamento Primário**: Firestore multi-região
- **Armazenamento Secundário**: PostgreSQL (para contingência e BI)
- **Integração**: Trigger Pub/Sub para replicação de dados Firestore → PostgreSQL
- **Autenticação**: JWT Bearer obrigatório em todas as rotas
- **Versionamento**: API versionada (/v1)
- **Formato**: Somente JSON, stateless
- **CORS**: Restrito a <https://portal.knnidiomas.com.br> e <http://localhost:5173>
- **Logs**: Estruturados com mascaramento de CPF

## 2. Estrutura de Dados (Coleções Firestore)

- **students**: { id, cpf_hash, name, email, course, active_until }
- **employees**: { id, tenant_id, cpf_hash, name, email, department, active }
- **partners**: { id, trade_name, category, address, active }
- **promotions**: { id, partner_id, title, type, target_profile, valid_from,
  valid_to, active }
- **validation_codes**: { id, student_id, partner_id, code_hash, expires,
  used_at }
- **redemptions**: { id, validation_code_id, value, used_at }

**Observação**: students, employees, partners e validation_codes são
replicados em PostgreSQL via worker para garantir leitura em modo degradado.

## 3. Rotas da API

### Perfil Comum

- **GET /health**: Verifica status da API (`"status":"ok","mode":"normal|degraded"`)

### Perfil Aluno (role=student)

- **GET /partners**: Lista parceiros com filtros/paginação
  - Parâmetros: cat (categoria), ord (ordenação)
- **GET /partners/{id}**: Detalhes do parceiro + promoções ativas
- **POST /validation-codes**: Gera código de validação de 6 dígitos
  (expira em 3 min)
  - Payload: { partner_id }
- **GET /students/me/history**: Histórico de resgates do aluno
- **GET /students/me/fav**: Lista parceiros favoritos
- **POST /students/me/fav**: Adiciona parceiro aos favoritos
- **DELETE /students/me/fav/{pid}**: Remove parceiro dos favoritos

### Perfil Funcionário (role=employee)

- **GET /employees/partners**: Lista parceiros com filtros/paginação
  - Parâmetros: cat (categoria), ord (ordenação)
- **GET /employees/partners/{id}**: Detalhes do parceiro + promoções ativas
  para funcionários
- **POST /employees/validation-codes**: Gera código de validação de 6 dígitos
  (expira em 3 min)
  - Payload: { partner_id }
- **GET /employees/me/history**: Histórico de resgates do funcionário
- **GET /employees/me/fav**: Lista parceiros favoritos
- **POST /employees/me/fav**: Adiciona parceiro aos favoritos
- **DELETE /employees/me/fav/{pid}**: Remove parceiro dos favoritos

### Perfil Parceiro (role=partner)

- **POST /partner/redeem**: Resgata código de validação
  - Payload: { code, cpf }
- **GET /partner/promotions**: Lista promoções do parceiro
- **POST /partner/promotions**: Cria nova promoção
- **PUT /partner/promotions/{id}**: Edita promoção existente
- **DELETE /partner/promotions/{id}**: Desativa promoção
- **GET /partner/reports**: Resumo de uso
  - Parâmetros: range (ex: 2025-05)

### Perfil Administrador (role=admin)

- **GET /admin/{entity}**: Lista entidades (students, partners, promotions)
- **POST /admin/{entity}**: Cria nova entidade
- **PUT /admin/{entity}/{id}**: Atualiza entidade existente
- **DELETE /admin/{entity}/{id}**: Remove/inativa entidade
- **GET /admin/metrics**: KPIs (alunos ativos, códigos gerados, top parceiros)
- **POST /admin/notifications**: Envia notificações push/e-mail para alunos ou parceiros

## 4. Regras de Negócio

- **Códigos de Validação**:
  - Sequência numérica de 000000 a 999999
  - TTL = 180 segundos (3 minutos)
  - Uso único (marcado com used_at após uso)
- **Validação de Aluno**:
  - Redeem por CPF só é permitido se active_until ≥ data atual
- **Rate-limit**:
  - Máximo 5 requisições POST /partner/redeem por minuto por IP
- **Promoções**:
  - Promoções expiradas não aparecem para alunos ou funcionários
  - Tentativa de resgate de promoção expirada retorna HTTP 410
  - Promoções são filtradas por target_profile:
    - Alunos veem apenas promoções com target_profile="student" ou "both"
    - Funcionários veem apenas promoções com target_profile="employee" ou "both"
- **Validação de Funcionário**:
  - Funcionário deve estar ativo (active=true) para gerar códigos de validação
- **Segurança de CPF**:
  - CPF nunca é armazenado em texto claro
  - Usar hash = sha256(cpf+salt)

## 5. Resiliência e Segurança

- **Verificação JWT**:
  - Assinatura verificada via JWKS
  - Cache de 10 minutos para JWKS
- **Circuit-breaker**:
  - 3 falhas consecutivas no Firestore ativam modo de contingência
  - Em contingência, leitura somente do PostgreSQL até sucesso no Firestore
- **Backup**:
  - Backup completo do Firestore para Cloud Storage
  - Caminho: gs://knn-backup/YYYYMMDD
  - Agendamento via Cloud Scheduler (02:00 UTC)
- **Testes**:
  - Pytest cobrindo happy path e erros (401/403/404/422)
  - Testes de rate-limit

## 6. Formato de Resposta

- **Sucesso**:

  ```json
  { "data": { ... }, "msg": "ok" }
  ```

- **Erro**:

  ```json
  { "error": { "code": "INVALID_CODE", "msg": "Código expirado ou já usado" } }
  ```

- **Códigos HTTP**:
  - 401: Token inválido
  - 403: Role negado
  - 404: Recurso não encontrado
  - 422: Erro de validação

## 7. Entregáveis

- **openapi.yaml**: Documentação completa da API
- **Dockerfile**: Configuração do contêiner
- **deploy_cloudrun.sh**: Script para deploy no Cloud Run
- **Testes Pytest**: Cobertura ≥ 90% das linhas de código
- **seed_dev.py**: Script para criar dados de teste (5 alunos, 3 parceiros, 4 promoções)
