from datetime import datetime, timedelta

import firebase_admin
import requests
from fastapi import FastAPI, HTTPException
from firebase_admin import credentials, storage

app = FastAPI()

# Inicializar Firebase Admin SDK
# Substitua pelo caminho do seu arquivo de credenciais
cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
firebase_admin.initialize_app(
    cred,
    {
        "storageBucket": "knn-benefits.firebasestorage.app"  # Seu bucket
    },
)

bucket = storage.bucket()


@app.get("/storage/url/{file_path:path}")
async def get_file_url_with_token(file_path: str, method: str = "signed"):
    """
    Obtém URL do arquivo no Firebase Storage com token

    Args:
        file_path: Caminho do arquivo (ex: "partners/logos/PTN_I2M5086_EDU.png")
        method: Método para obter a URL ('signed', 'public', 'download_token')
    """
    try:
        # Método 1: URL Assinada (Recomendado)
        if method == "signed":
            return await get_signed_url(file_path)

        # Método 2: URL Pública com Download Token
        elif method == "public":
            return await get_public_url_with_token(file_path)

        # Método 3: URL com Download Token customizado
        elif method == "download_token":
            return await get_url_with_download_token(file_path)

        else:
            raise HTTPException(status_code=400, detail="Método inválido")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter URL: {str(e)}")


async def get_signed_url(file_path: str) -> dict:
    """
    Método 1: URL Assinada (mais seguro e flexível)
    Gera uma URL temporária com tempo de expiração
    """
    blob = bucket.blob(file_path)

    # Gerar URL assinada válida por 1 hora
    expiration_time = datetime.utcnow() + timedelta(hours=1)

    signed_url = blob.generate_signed_url(expiration=expiration_time, method="GET")

    return {
        "url": signed_url,
        "method": "signed_url",
        "expires_at": expiration_time.isoformat(),
        "file_path": file_path,
    }


async def get_public_url_with_token(file_path: str) -> dict:
    """
    Método 2: URL Pública com Download Token
    Obtém a URL pública que já possui token
    """
    blob = bucket.blob(file_path)

    # Verificar se o arquivo existe
    if not blob.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    # Obter metadados do arquivo
    blob.reload()

    # Construir URL pública
    bucket_name = bucket.name
    encoded_path = requests.utils.quote(file_path, safe="")

    # Se o arquivo tem downloadTokens nos metadados
    download_tokens = blob.metadata.get("downloadTokens") if blob.metadata else None

    if download_tokens:
        # Usar o primeiro token disponível
        token = download_tokens.split(",")[0]
        public_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket_name}/o/{encoded_path}?alt=media&token={token}"
    else:
        # URL sem token (apenas para arquivos públicos)
        public_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket_name}/o/{encoded_path}?alt=media"

    return {
        "url": public_url,
        "method": "public_with_token",
        "has_token": download_tokens is not None,
        "file_path": file_path,
    }


async def get_url_with_download_token(file_path: str) -> dict:
    """
    Método 3: Criar/Obter Download Token customizado
    """
    blob = bucket.blob(file_path)

    # Verificar se o arquivo existe
    if not blob.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    # Obter metadados atuais
    blob.reload()

    # Se não existe downloadTokens, criar um novo
    if not blob.metadata or "downloadTokens" not in blob.metadata:
        import uuid

        new_token = str(uuid.uuid4())

        # Atualizar metadados com novo token
        blob.metadata = blob.metadata or {}
        blob.metadata["downloadTokens"] = new_token
        blob.patch()

        token = new_token
    else:
        # Usar token existente
        token = blob.metadata["downloadTokens"].split(",")[0]

    # Construir URL
    bucket_name = bucket.name
    encoded_path = requests.utils.quote(file_path, safe="")
    url_with_token = f"https://firebasestorage.googleapis.com/v0/b/{bucket_name}/o/{encoded_path}?alt=media&token={token}"

    return {
        "url": url_with_token,
        "method": "download_token",
        "token": token,
        "file_path": file_path,
    }


@app.post("/storage/upload-and-get-url")
async def upload_file_and_get_url(file_path: str, file_content: bytes):
    """
    Upload de arquivo e retorno da URL com token
    """
    try:
        blob = bucket.blob(file_path)

        # Upload do arquivo
        blob.upload_from_string(file_content)

        # Tornar público (opcional)
        blob.make_public()

        # Obter URL com token
        url_info = await get_public_url_with_token(file_path)

        return {"message": "Arquivo enviado com sucesso", "file_info": url_info}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")


@app.get("/storage/file-info/{file_path:path}")
async def get_file_info(file_path: str):
    """
    Obter informações detalhadas do arquivo
    """
    try:
        blob = bucket.blob(file_path)

        if not blob.exists():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")

        blob.reload()

        return {
            "name": blob.name,
            "size": blob.size,
            "content_type": blob.content_type,
            "created": blob.time_created.isoformat() if blob.time_created else None,
            "updated": blob.updated.isoformat() if blob.updated else None,
            "metadata": blob.metadata,
            "download_tokens": blob.metadata.get("downloadTokens")
            if blob.metadata
            else None,
            "public_url": blob.public_url,
            "media_link": blob.media_link,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter informações: {str(e)}"
        )


# Exemplo de uso com diferentes configurações
@app.get("/storage/url-examples/{file_path:path}")
async def get_url_examples(file_path: str):
    """
    Retorna exemplos de diferentes tipos de URL para o mesmo arquivo
    """
    try:
        results = {}

        # URL Assinada
        try:
            results["signed_url"] = await get_signed_url(file_path)
        except Exception as e:
            results["signed_url"] = {"error": str(e)}

        # URL Pública com token
        try:
            results["public_url"] = await get_public_url_with_token(file_path)
        except Exception as e:
            results["public_url"] = {"error": str(e)}

        # URL com download token
        try:
            results["download_token_url"] = await get_url_with_download_token(file_path)
        except Exception as e:
            results["download_token_url"] = {"error": str(e)}

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
