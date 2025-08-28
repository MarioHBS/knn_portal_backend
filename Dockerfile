FROM python:3.13-slim

WORKDIR /app

# Criar usuário não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependências do sistema e atualizações de segurança
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copiar arquivos de requisitos primeiro para aproveitar o cache de camadas
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY ./src /app/src

# Configurar variáveis de ambiente
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

# Definir permissões de segurança para o diretório da aplicação
RUN chown -R appuser:appuser /app

# Mudar para usuário não-root
USER appuser

# Expor a porta que será usada pelo Cloud Run
EXPOSE 8080

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
