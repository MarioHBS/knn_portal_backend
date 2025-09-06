#!/usr/bin/env python3
"""
Configuração do Firebase Storage para upload de imagens
Prepara estrutura para upload de logos e outras imagens de parceiros
"""

import mimetypes
from pathlib import Path
from typing import Any

# Configurações do Firebase Storage
STORAGE_BUCKET = "knn-benefits.firebasestorage.app"  # Bucket principal do projeto

# Estrutura de pastas no Storage
STORAGE_PATHS = {
    "partners": {
        "logos": "partners/logos/",
        "faixadas": "partners/faixadas/",
        "outros": "partners/outros/",
    },
    "temp": "temp/",
    "uploads": "uploads/",
}

# Configurações de imagem
IMAGE_CONFIG = {
    "allowed_extensions": [".png", ".jpg", ".jpeg", ".webp"],
    "max_file_size": 5 * 1024 * 1024,  # 5MB
    "logo_max_dimensions": (400, 400),
    "faixada_max_dimensions": (800, 600),
    "quality": 85,
}

# Metadados padrão para uploads
DEFAULT_METADATA = {
    "cacheControl": "public, max-age=31536000",  # 1 ano
    "contentDisposition": "inline",
}


def get_storage_path(category: str, subcategory: str = None) -> str:
    """
    Retorna o caminho no Storage baseado na categoria

    Args:
        category: Categoria principal (ex: 'partners')
        subcategory: Subcategoria (ex: 'logos', 'faixadas')

    Returns:
        Caminho completo no Storage
    """
    if category in STORAGE_PATHS:
        if subcategory and isinstance(STORAGE_PATHS[category], dict):
            return STORAGE_PATHS[category].get(
                subcategory, STORAGE_PATHS[category]["outros"]
            )
        elif isinstance(STORAGE_PATHS[category], str):
            return STORAGE_PATHS[category]

    return STORAGE_PATHS["uploads"]


def get_file_metadata(file_path: Path, partner_id: str = None) -> dict[str, Any]:
    """
    Gera metadados para o arquivo

    Args:
        file_path: Caminho do arquivo local
        partner_id: ID do parceiro (opcional)

    Returns:
        Dicionário com metadados
    """
    metadata = DEFAULT_METADATA.copy()

    # Detecta tipo MIME
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type:
        metadata["contentType"] = mime_type

    # Adiciona metadados customizados
    custom_metadata = {
        "uploadedBy": "knn-portal-system",
        "originalName": file_path.name,
        "category": categorize_image_file(file_path.name),
    }

    if partner_id:
        custom_metadata["partnerId"] = partner_id

    metadata["customMetadata"] = custom_metadata

    return metadata


def categorize_image_file(filename: str) -> str:
    """
    Categoriza arquivo de imagem baseado no nome

    Args:
        filename: Nome do arquivo

    Returns:
        Categoria da imagem
    """
    filename_lower = filename.lower()

    if "_logo." in filename_lower:
        return "logo"
    elif "_faixada." in filename_lower:
        return "faixada"
    else:
        return "outros"


def generate_storage_filename(original_filename: str, partner_id: str = None) -> str:
    """
    Gera nome do arquivo para o Storage

    Args:
        original_filename: Nome original do arquivo
        partner_id: ID do parceiro (opcional)

    Returns:
        Nome do arquivo para o Storage
    """
    # Extrai informações do nome original
    path = Path(original_filename)

    # Se já tem padrão PTN_, mantém
    if original_filename.startswith("PTN_"):
        return original_filename

    # Caso contrário, gera novo nome
    if partner_id:
        category = categorize_image_file(original_filename)
        return f"{partner_id}_{category}{path.suffix}"

    return original_filename


def validate_image_file(file_path: Path) -> dict[str, Any]:
    """
    Valida arquivo de imagem

    Args:
        file_path: Caminho do arquivo

    Returns:
        Dicionário com resultado da validação
    """
    result = {"valid": False, "errors": [], "warnings": []}

    # Verifica se arquivo existe
    if not file_path.exists():
        result["errors"].append("Arquivo não encontrado")
        return result

    # Verifica extensão
    if file_path.suffix.lower() not in IMAGE_CONFIG["allowed_extensions"]:
        result["errors"].append(f"Extensão não permitida: {file_path.suffix}")

    # Verifica tamanho
    file_size = file_path.stat().st_size
    if file_size > IMAGE_CONFIG["max_file_size"]:
        result["errors"].append(f"Arquivo muito grande: {file_size} bytes")

    # Se não há erros, é válido
    if not result["errors"]:
        result["valid"] = True

    return result


# Configuração das regras de segurança do Storage (para referência)
STORAGE_RULES = """
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Regras para imagens de parceiros
    match /partners/{imageType}/{imageId} {
      // Leitura permitida para usuários autenticados
      allow read: if request.auth != null;

      // Upload permitido apenas para admins
      allow write: if request.auth != null
                   && request.auth.token.admin == true
                   && resource.size < 5 * 1024 * 1024  // 5MB
                   && request.resource.contentType.matches('image/.*');
    }

    // Pasta temporária para uploads
    match /temp/{allPaths=**} {
      allow read, write: if request.auth != null
                         && request.auth.token.admin == true;
    }

    // Pasta de uploads gerais
    match /uploads/{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null
                   && request.auth.token.admin == true;
    }
  }
}
"""

# URLs públicas para desenvolvimento (ajustar conforme necessário)
DEV_IMAGE_URLS = {
    "base_url": f"https://firebasestorage.googleapis.com/v0/b/{STORAGE_BUCKET}/o/",
    "url_suffix": "?alt=media",
}


def get_public_url(storage_path: str) -> str:
    """
    Gera URL pública para imagem no Storage

    Args:
        storage_path: Caminho da imagem no Storage

    Returns:
        URL pública da imagem
    """
    # Codifica o caminho para URL
    encoded_path = storage_path.replace("/", "%2F")
    return f"{DEV_IMAGE_URLS['base_url']}{encoded_path}{DEV_IMAGE_URLS['url_suffix']}"


def get_local_dev_url(filename: str) -> str:
    """
    Gera URL local para desenvolvimento

    Args:
        filename: Nome do arquivo

    Returns:
        URL local para desenvolvimento
    """
    return f"/statics/logos/{filename}"


# Configuração para ambiente de desenvolvimento
DEV_CONFIG = {
    "use_local_files": True,  # Usar arquivos locais em desenvolvimento
    "local_base_path": "statics/logos/",
    "upload_on_save": False,  # Não fazer upload automático em dev
    "generate_thumbnails": False,  # Não gerar thumbnails em dev
}

# Configuração para ambiente de produção
PROD_CONFIG = {
    "use_local_files": False,
    "local_base_path": None,
    "upload_on_save": True,
    "generate_thumbnails": True,
}


def get_config(environment: str = "development") -> dict[str, Any]:
    """
    Retorna configuração baseada no ambiente

    Args:
        environment: Ambiente ('development' ou 'production')

    Returns:
        Configuração do ambiente
    """
    if environment == "production":
        return PROD_CONFIG
    return DEV_CONFIG
