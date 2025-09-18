# Configuração do GitHub Actions - CI/CD

Este documento descreve como configurar o CI/CD com GitHub Actions para o Portal de Benefícios KNN.

## Visão Geral

O projeto possui 3 workflows principais:

1. **CI (Integração Contínua)** - `.github/workflows/ci.yml`
2. **CD (Deploy Contínuo)** - `.github/workflows/cd.yml`
3. **Validação de PR** - `.github/workflows/pr-validation.yml`

## Configuração dos Secrets

### Secrets Obrigatórios

Configure os seguintes secrets no GitHub (Settings > Secrets and variables > Actions):

#### 1. Google Cloud Platform

```bash
GCP_SA_KEY              # Chave JSON da Service Account (formato JSON completo)
GCP_PROJECT_ID          # ID do projeto no Google Cloud (ex: knn-benefits)
```

#### 2. Variáveis de Ambiente da Aplicação

```bash
POSTGRES_CONNECTION_STRING  # String de conexão PostgreSQL
JWKS_URL                   # URL do JWKS para validação JWT
CNPJ_HASH_SALT            # Salt para hash de CNPJ
```

### Como Obter a Service Account Key

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Vá para **IAM & Admin > Service Accounts**
3. Crie uma nova Service Account ou use uma existente
4. Adicione as seguintes permissões:
   - Cloud Run Admin
   - Cloud Build Editor
   - Container Registry Service Agent
   - Storage Admin
5. Gere uma chave JSON e copie todo o conteúdo para o secret `GCP_SA_KEY`

### Exemplo de Service Account Key

```json
{
  "type": "service_account",
  "project_id": "knn-benefits",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "github-actions@knn-benefits.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

## Fluxo de Deploy

### Branch Master

- ✅ Executa CI completo (testes, linting, segurança)
- ✅ Deploy automático para produção no Google Cloud Run
- ✅ Testa endpoint de health após deploy

### Outras Branches

- ✅ Executa apenas CI (testes, linting, segurança)
- ❌ Não faz deploy

### Pull Requests

- ✅ Executa CI completo
- ✅ Valida título do PR (conventional commits)
- ✅ Verifica arquivos modificados
- ✅ Sugere adição de testes para novos arquivos

## Configuração do Projeto

### Configurações Atuais (baseadas no deploy_cloudrun.sh)

```yaml
Projeto GCP: knn-benefits (ou knn-portal-prod)
Serviço: portal-beneficios-api
Região: us-central1
Memória: 512Mi
CPU: 1
Concorrência: 80
Instâncias máximas: 10
```

### Variáveis de Ambiente Configuradas

```yaml
MODE: production
FIRESTORE_PROJECT: {GCP_PROJECT_ID}
POSTGRES_CONNECTION_STRING: {secret}
JWKS_URL: {secret}
JWKS_CACHE_TTL: 600
CNPJ_HASH_SALT: {secret}
```

## Monitoramento

### Logs de Deploy

- Acesse **Actions** no GitHub para ver logs detalhados
- Cada deploy gera uma tag única com timestamp
- URL do serviço é exibida após deploy bem-sucedido

### Health Check

- Endpoint testado automaticamente: `/v1/health`
- Deploy falha se health check não responder

### Notificações

- ✅ Sucesso: Exibe URL e versão deployada
- ❌ Falha: Indica onde verificar logs

## Troubleshooting

### Erro de Autenticação

```bash
# Verificar se a Service Account tem as permissões corretas
gcloud projects get-iam-policy knn-benefits
```

### Erro de Build

```bash
# Verificar se o Dockerfile está correto
# Verificar se todas as dependências estão no requirements.txt
```

### Erro de Deploy

```bash
# Verificar se o serviço já existe no Cloud Run
gcloud run services list --region=us-central1
```

### Testes Falhando

```bash
# Verificar se TESTING_MODE está configurado
# Verificar se os mocks estão funcionando corretamente
```

## Próximos Passos

1. Configure os secrets no GitHub
2. Faça um push para a branch master
3. Acompanhe o deploy nos Actions
4. Verifique se o serviço está funcionando

## Comandos Úteis

```bash
# Verificar status do serviço
gcloud run services describe portal-beneficios-api --region=us-central1

# Ver logs do Cloud Run
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=portal-beneficios-api" --limit=50

# Testar localmente
python scripts/run_server.py
```
