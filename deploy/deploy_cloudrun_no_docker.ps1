# Deploy para Cloud Run sem Docker - usando buildpacks
# Script PowerShell para Windows

# Configurações do projeto
$PROJECT_ID = "knn-benefits"
$SERVICE_NAME = "knn-portal-backend"
$REGION = "us-central1"

Write-Host "=== Deploy Cloud Run sem Docker ===" -ForegroundColor Green
Write-Host "Projeto: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Serviço: $SERVICE_NAME" -ForegroundColor Yellow
Write-Host "Região: $REGION" -ForegroundColor Yellow

# Verificar autenticação do gcloud
Write-Host "`n1. Verificando autenticação do gcloud..." -ForegroundColor Cyan
try {
    $auth_check = gcloud auth print-access-token 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro: gcloud não está autenticado" -ForegroundColor Red
        Write-Host "Execute: gcloud auth login" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ gcloud autenticado com sucesso" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro ao verificar autenticação: $_" -ForegroundColor Red
    exit 1
}

# Configurar projeto
Write-Host "`n2. Configurando projeto..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao configurar projeto" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Projeto configurado: $PROJECT_ID" -ForegroundColor Green

# Habilitar APIs necessárias
Write-Host "`n3. Verificando APIs necessárias..." -ForegroundColor Cyan
$apis = @("run.googleapis.com", "cloudbuild.googleapis.com")
foreach ($api in $apis) {
    Write-Host "Habilitando $api..." -ForegroundColor Yellow
    gcloud services enable $api --quiet
}
Write-Host "✅ APIs habilitadas" -ForegroundColor Green

# Fazer deploy usando source code (buildpacks)
Write-Host "`n4. Fazendo deploy do source code..." -ForegroundColor Cyan
Write-Host "Isso pode levar alguns minutos..." -ForegroundColor Yellow

$env_vars = "MODE=production,FIRESTORE_PROJECT=$PROJECT_ID,POSTGRES_CONNECTION_STRING=$env:POSTGRES_CONNECTION_STRING,JWKS_URL=$env:JWKS_URL,CNPJ_HASH_SALT=$env:CNPJ_HASH_SALT"

gcloud run deploy $SERVICE_NAME `
    --source . `
    --region $REGION `
    --allow-unauthenticated `
    --platform managed `
    --memory 1Gi `
    --cpu 1 `
    --concurrency 100 `
    --max-instances 10 `
    --min-instances 0 `
    --port 8080 `
    --set-env-vars $env_vars `
    --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro durante o deploy" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Deploy concluído com sucesso!" -ForegroundColor Green

# Obter URL do serviço
Write-Host "`n5. Obtendo URL do serviço..." -ForegroundColor Cyan
$service_url = gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao obter URL do serviço" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Serviço disponível em: $service_url" -ForegroundColor Green

# Testar endpoint de health
Write-Host "`n6. Testando endpoint de health..." -ForegroundColor Cyan
$health_url = "$service_url/health"
Write-Host "Testando: $health_url" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri $health_url -Method GET -TimeoutSec 30
    Write-Host "✅ Health check passou!" -ForegroundColor Green
    Write-Host "Resposta: $($response | ConvertTo-Json -Compress)" -ForegroundColor White
} catch {
    Write-Host "⚠️  Health check falhou: $_" -ForegroundColor Yellow
    Write-Host "O serviço pode ainda estar inicializando..." -ForegroundColor Yellow
}

Write-Host "`n=== Deploy Concluído ===" -ForegroundColor Green
Write-Host "URL do serviço: $service_url" -ForegroundColor White
Write-Host "Health endpoint: $health_url" -ForegroundColor White
Write-Host "`nPara ver logs:" -ForegroundColor Cyan
Write-Host "gcloud run services logs read $SERVICE_NAME --region=$REGION" -ForegroundColor White