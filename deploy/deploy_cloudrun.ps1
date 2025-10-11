# Script PowerShell para deploy do Portal de Benefícios KNN no Cloud Run
# Adaptado para Windows

param(
    [string]$ProjectId = "knn-portal-prod",
    [string]$ServiceName = "portal-beneficios-api",
    [string]$Region = "us-central1"
)

# Configurações
$IMAGE_NAME = "gcr.io/$ProjectId/$ServiceName"
$TAG = Get-Date -Format "yyyyMMdd-HHmmss"

# Função para escrever mensagens coloridas
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Yellow "Iniciando deploy do Portal de Benefícios KNN para Cloud Run..."

# Verificar se gcloud está autenticado
try {
    $null = gcloud auth print-access-token 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Não autenticado"
    }
}
catch {
    Write-ColorOutput Red "Erro: Não autenticado no Google Cloud. Execute 'gcloud auth login' primeiro."
    exit 1
}

# Verificar se o projeto existe e está configurado
Write-ColorOutput Yellow "Configurando projeto $ProjectId..."
gcloud config set project $ProjectId
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Erro ao configurar projeto $ProjectId"
    exit 1
}

# Verificar se Docker está rodando
Write-ColorOutput Yellow "Verificando se Docker está rodando..."
try {
    $null = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker não está rodando"
    }
}
catch {
    Write-ColorOutput Red "Docker Desktop não está rodando!"
    Write-ColorOutput Yellow "Por favor:"
    Write-ColorOutput Yellow "1. Inicie o Docker Desktop manualmente"
    Write-ColorOutput Yellow "2. Aguarde até que esteja completamente carregado"
    Write-ColorOutput Yellow "3. Execute este script novamente"
    Write-ColorOutput Yellow ""
    Write-ColorOutput Yellow "Tentando iniciar Docker Desktop automaticamente..."
    
    try {
        Start-Process "Docker Desktop" -WindowStyle Hidden
        Write-ColorOutput Yellow "Aguardando Docker Desktop inicializar (60 segundos)..."
        
        $timeout = 60
        $elapsed = 0
        while ($elapsed -lt $timeout) {
            Start-Sleep 5
            $elapsed += 5
            try {
                $null = docker info 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-ColorOutput Green "Docker Desktop iniciado com sucesso!"
                    break
                }
            }
            catch {
                # Continue tentando
            }
            Write-ColorOutput Yellow "Aguardando... ($elapsed/$timeout segundos)"
        }
        
        if ($elapsed -ge $timeout) {
            Write-ColorOutput Red "Timeout: Docker Desktop não iniciou em $timeout segundos"
            Write-ColorOutput Yellow "Inicie o Docker Desktop manualmente e execute o script novamente"
            exit 1
        }
    }
    catch {
        Write-ColorOutput Red "Erro ao tentar iniciar Docker Desktop: $($_.Exception.Message)"
        Write-ColorOutput Yellow "Inicie o Docker Desktop manualmente e execute o script novamente"
        exit 1
    }
}

# Construir a imagem Docker
Write-ColorOutput Yellow "Construindo imagem Docker..."
docker build -t "${IMAGE_NAME}:${TAG}" .
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Erro ao construir imagem Docker"
    exit 1
}

docker tag "${IMAGE_NAME}:${TAG}" "${IMAGE_NAME}:latest"
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Erro ao criar tag latest"
    exit 1
}

# Enviar a imagem para o Container Registry
Write-ColorOutput Yellow "Enviando imagem para Container Registry..."
docker push "${IMAGE_NAME}:${TAG}"
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Erro ao enviar imagem com tag $TAG"
    exit 1
}

docker push "${IMAGE_NAME}:latest"
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Erro ao enviar imagem latest"
    exit 1
}

# Implantar no Cloud Run
Write-ColorOutput Yellow "Implantando no Cloud Run..."

# Verificar se as variáveis de ambiente necessárias estão definidas
if (-not $env:POSTGRES_CONNECTION_STRING) {
    Write-ColorOutput Red "Aviso: POSTGRES_CONNECTION_STRING não está definida"
}
if (-not $env:JWKS_URL) {
    Write-ColorOutput Red "Aviso: JWKS_URL não está definida"
}
if (-not $env:CNPJ_HASH_SALT) {
    Write-ColorOutput Red "Aviso: CNPJ_HASH_SALT não está definida"
}

$deployArgs = @(
    "run", "deploy", $ServiceName,
    "--image", "${IMAGE_NAME}:${TAG}",
    "--platform", "managed",
    "--region", $Region,
    "--allow-unauthenticated",
    "--memory", "512Mi",
    "--cpu", "1",
    "--concurrency", "80",
    "--max-instances", "10",
    "--set-env-vars", "MODE=production",
    "--set-env-vars", "FIRESTORE_PROJECT=$ProjectId"
)

# Adicionar variáveis de ambiente opcionais se estiverem definidas
if ($env:POSTGRES_CONNECTION_STRING) {
    $deployArgs += "--set-env-vars", "POSTGRES_CONNECTION_STRING=$env:POSTGRES_CONNECTION_STRING"
}
if ($env:JWKS_URL) {
    $deployArgs += "--set-env-vars", "JWKS_URL=$env:JWKS_URL"
}
if ($env:CNPJ_HASH_SALT) {
    $deployArgs += "--set-env-vars", "CNPJ_HASH_SALT=$env:CNPJ_HASH_SALT"
}

$deployArgs += "--set-env-vars", "JWKS_CACHE_TTL=600"

& gcloud @deployArgs
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Erro ao fazer deploy no Cloud Run"
    exit 1
}

# Obter a URL do serviço
Write-ColorOutput Yellow "Obtendo URL do serviço..."
$SERVICE_URL = gcloud run services describe $ServiceName --region $Region --format="value(status.url)"
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Erro ao obter URL do serviço"
    exit 1
}

Write-ColorOutput Green "Deploy concluído com sucesso!"
Write-ColorOutput Green "Serviço disponível em: $SERVICE_URL"
Write-ColorOutput Green "Versão implantada: $TAG"

# Testar o endpoint de health
Write-ColorOutput Yellow "Testando endpoint de health..."
try {
    $healthResponse = Invoke-RestMethod -Uri "$SERVICE_URL/v1/health" -Method Get -TimeoutSec 30
    Write-ColorOutput Green "Health check passou:"
    $healthResponse | ConvertTo-Json -Depth 3
}
catch {
    Write-ColorOutput Red "Erro ao testar endpoint de health: $($_.Exception.Message)"
    Write-ColorOutput Yellow "Verifique manualmente: $SERVICE_URL/v1/health"
}

Write-ColorOutput Green "Tudo pronto!"
Write-ColorOutput Green "Documentação da API disponível em: $SERVICE_URL/v1/docs"