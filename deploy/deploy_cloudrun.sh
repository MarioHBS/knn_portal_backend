#!/bin/bash
set -e

# Configurações
PROJECT_ID=${PROJECT_ID:-"knn-portal-prod"}
SERVICE_NAME=${SERVICE_NAME:-"portal-beneficios-api"}
REGION=${REGION:-"us-central1"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
TAG=$(date +%Y%m%d-%H%M%S)

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Iniciando deploy do Portal de Benefícios KNN para Cloud Run...${NC}"

# Verificar se gcloud está autenticado
if ! gcloud auth print-access-token &>/dev/null; then
  echo "Erro: Não autenticado no Google Cloud. Execute 'gcloud auth login' primeiro."
  exit 1
fi

# Verificar se o projeto existe e está configurado
echo -e "${YELLOW}Configurando projeto ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Construir a imagem Docker
echo -e "${YELLOW}Construindo imagem Docker...${NC}"
docker build -t ${IMAGE_NAME}:${TAG} .
docker tag ${IMAGE_NAME}:${TAG} ${IMAGE_NAME}:latest

# Enviar a imagem para o Container Registry
echo -e "${YELLOW}Enviando imagem para Container Registry...${NC}"
docker push ${IMAGE_NAME}:${TAG}
docker push ${IMAGE_NAME}:latest

# Implantar no Cloud Run
echo -e "${YELLOW}Implantando no Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:${TAG} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 10 \
  --set-env-vars="MODE=production" \
  --set-env-vars="FIRESTORE_PROJECT=${PROJECT_ID}" \
  --set-env-vars="POSTGRES_CONNECTION_STRING=${POSTGRES_CONNECTION_STRING}" \
  --set-env-vars="JWKS_URL=${JWKS_URL}" \
  --set-env-vars="JWKS_CACHE_TTL=600" \
  --set-env-vars="CNPJ_HASH_SALT=${CNPJ_HASH_SALT}"

# Obter a URL do serviço
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)')

echo -e "${GREEN}Deploy concluído com sucesso!${NC}"
echo -e "Serviço disponível em: ${SERVICE_URL}"
echo -e "Versão implantada: ${TAG}"

# Testar o endpoint de health
echo -e "${YELLOW}Testando endpoint de health...${NC}"
curl -s "${SERVICE_URL}/v1/health" | jq .

echo -e "${GREEN}Tudo pronto!${NC}"
