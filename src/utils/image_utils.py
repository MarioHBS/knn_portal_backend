#!/usr/bin/env python3
"""
Utilitários para processamento e upload de imagens
Integração com Firebase Storage para imagens de parceiros
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Adiciona o diretório raiz ao path para imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import firebase_admin
    from firebase_admin import credentials, storage

    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Firebase Admin SDK não disponível. Funcionalidades de upload desabilitadas.")

from firebase_storage_config import (
    categorize_image_file,
    generate_storage_filename,
    get_config,
    get_file_metadata,
    get_local_dev_url,
    get_public_url,
    get_storage_path,
    validate_image_file,
)


class ImageManager:
    """
    Gerenciador de imagens para o sistema
    Suporta tanto desenvolvimento local quanto produção com Firebase Storage
    """

    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.config = get_config(environment)
        self.firebase_initialized = False

        if FIREBASE_AVAILABLE and environment == "production":
            self._initialize_firebase()

    def _initialize_firebase(self):
        """Inicializa Firebase Admin SDK"""
        try:
            # Verifica se já foi inicializado
            if not firebase_admin._apps:
                # Tenta usar credenciais padrão ou arquivo de service account
                cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                if cred_path and Path(cred_path).exists():
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                else:
                    # Usa credenciais padrão do ambiente
                    firebase_admin.initialize_app()

            self.firebase_initialized = True
            print("Firebase Storage inicializado com sucesso")

        except Exception as e:
            print(f"Erro ao inicializar Firebase: {e}")
            self.firebase_initialized = False

    def validate_image(self, file_path: Path) -> dict[str, Any]:
        """
        Valida arquivo de imagem

        Args:
            file_path: Caminho do arquivo

        Returns:
            Resultado da validação
        """
        return validate_image_file(file_path)

    def get_image_url(self, filename: str, partner_id: str = None) -> str:
        """
        Retorna URL da imagem baseada no ambiente

        Args:
            filename: Nome do arquivo
            partner_id: ID do parceiro (opcional)

        Returns:
            URL da imagem
        """
        if self.config["use_local_files"]:
            return get_local_dev_url(filename)
        else:
            category = categorize_image_file(filename)
            storage_path = get_storage_path("partners", category) + filename
            return get_public_url(storage_path)

    def list_local_images(self, category: str = "logos") -> list[dict[str, Any]]:
        """
        Lista imagens locais na pasta statics

        Args:
            category: Categoria das imagens

        Returns:
            Lista de informações das imagens
        """
        images = []
        local_path = Path(f"statics/{category}")

        if not local_path.exists():
            return images

        for image_file in local_path.glob("*.png"):
            try:
                stat = image_file.stat()
                images.append(
                    {
                        "filename": image_file.name,
                        "path": str(image_file),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "category": categorize_image_file(image_file.name),
                        "url": self.get_image_url(image_file.name),
                        "partner_id": self._extract_partner_id(image_file.name),
                    }
                )
            except Exception as e:
                print(f"Erro ao processar {image_file.name}: {e}")

        return sorted(images, key=lambda x: x["filename"])

    def _extract_partner_id(self, filename: str) -> str | None:
        """
        Extrai ID do parceiro do nome do arquivo

        Args:
            filename: Nome do arquivo

        Returns:
            ID do parceiro ou None
        """
        if filename.startswith("PTN_"):
            parts = filename.split("_")
            if len(parts) >= 3:
                return f"{parts[0]}_{parts[1]}_{parts[2]}"
        return None

    def upload_image(self, local_path: Path, partner_id: str = None) -> dict[str, Any]:
        """
        Faz upload de imagem para Firebase Storage

        Args:
            local_path: Caminho local da imagem
            partner_id: ID do parceiro (opcional)

        Returns:
            Resultado do upload
        """
        result = {"success": False, "url": None, "storage_path": None, "error": None}

        # Valida arquivo
        validation = self.validate_image(local_path)
        if not validation["valid"]:
            result["error"] = f"Arquivo inválido: {', '.join(validation['errors'])}"
            return result

        # Em desenvolvimento, apenas copia para pasta local
        if self.config["use_local_files"]:
            try:
                category = categorize_image_file(local_path.name)
                target_dir = Path(f"statics/{category}")
                target_dir.mkdir(parents=True, exist_ok=True)

                target_path = target_dir / local_path.name
                if local_path != target_path:
                    import shutil

                    shutil.copy2(local_path, target_path)

                result["success"] = True
                result["url"] = self.get_image_url(local_path.name)
                result["storage_path"] = str(target_path)

            except Exception as e:
                result["error"] = f"Erro ao copiar arquivo: {e}"

            return result

        # Upload para Firebase Storage (produção)
        if not self.firebase_initialized:
            result["error"] = "Firebase Storage não inicializado"
            return result

        try:
            bucket = storage.bucket()
            category = categorize_image_file(local_path.name)
            storage_filename = generate_storage_filename(local_path.name, partner_id)
            storage_path = get_storage_path("partners", category) + storage_filename

            # Upload do arquivo
            blob = bucket.blob(storage_path)
            metadata = get_file_metadata(local_path, partner_id)

            blob.upload_from_filename(
                str(local_path), content_type=metadata.get("contentType"), timeout=300
            )

            # Define metadados
            if "customMetadata" in metadata:
                blob.metadata = metadata["customMetadata"]
                blob.patch()

            # Define cache control
            if "cacheControl" in metadata:
                blob.cache_control = metadata["cacheControl"]
                blob.patch()

            result["success"] = True
            result["url"] = get_public_url(storage_path)
            result["storage_path"] = storage_path

        except Exception as e:
            result["error"] = f"Erro no upload: {e}"

        return result

    def batch_upload_images(self, image_paths: list[Path]) -> dict[str, Any]:
        """
        Faz upload em lote de múltiplas imagens

        Args:
            image_paths: Lista de caminhos das imagens

        Returns:
            Resultado do upload em lote
        """
        results = {
            "total": len(image_paths),
            "successful": 0,
            "failed": 0,
            "details": [],
            "errors": [],
        }

        for image_path in image_paths:
            try:
                partner_id = self._extract_partner_id(image_path.name)
                upload_result = self.upload_image(image_path, partner_id)

                if upload_result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        f"{image_path.name}: {upload_result['error']}"
                    )

                results["details"].append(
                    {
                        "filename": image_path.name,
                        "success": upload_result["success"],
                        "url": upload_result["url"],
                        "error": upload_result.get("error"),
                    }
                )

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{image_path.name}: {e}")

        return results

    def sync_local_to_storage(self) -> dict[str, Any]:
        """
        Sincroniza imagens locais com Firebase Storage

        Returns:
            Resultado da sincronização
        """
        if self.config["use_local_files"]:
            return {
                "success": False,
                "error": "Sincronização não disponível em modo de desenvolvimento",
            }

        # Lista imagens locais
        local_images = self.list_local_images()
        image_paths = [Path(img["path"]) for img in local_images]

        # Faz upload em lote
        return self.batch_upload_images(image_paths)

    def get_partner_images(self, partner_id: str) -> list[dict[str, Any]]:
        """
        Retorna todas as imagens de um parceiro específico

        Args:
            partner_id: ID do parceiro

        Returns:
            Lista de imagens do parceiro
        """
        all_images = self.list_local_images()
        return [img for img in all_images if img["partner_id"] == partner_id]

    def generate_image_report(self) -> dict[str, Any]:
        """
        Gera relatório completo das imagens

        Returns:
            Relatório das imagens
        """
        images = self.list_local_images()

        # Estatísticas por categoria
        categories = {}
        partners = set()
        total_size = 0

        for img in images:
            category = img["category"]
            categories[category] = categories.get(category, 0) + 1

            if img["partner_id"]:
                partners.add(img["partner_id"])

            total_size += img["size"]

        return {
            "total_images": len(images),
            "total_partners": len(partners),
            "total_size_bytes": total_size,
            "categories": categories,
            "images": images,
            "environment": self.environment,
            "firebase_available": self.firebase_initialized,
        }


# Instância global para uso fácil
image_manager = ImageManager()


# Funções de conveniência
def get_partner_logo_url(partner_id: str) -> str | None:
    """
    Retorna URL do logo de um parceiro

    Args:
        partner_id: ID do parceiro

    Returns:
        URL do logo ou None
    """
    images = image_manager.get_partner_images(partner_id)
    logos = [img for img in images if img["category"] == "logo"]

    if logos:
        return logos[0]["url"]

    return None


def list_all_partner_images() -> list[dict[str, Any]]:
    """
    Lista todas as imagens de parceiros

    Returns:
        Lista de todas as imagens
    """
    return image_manager.list_local_images()


def upload_partner_image(image_path: str, partner_id: str = None) -> dict[str, Any]:
    """
    Faz upload de uma imagem de parceiro

    Args:
        image_path: Caminho da imagem
        partner_id: ID do parceiro

    Returns:
        Resultado do upload
    """
    return image_manager.upload_image(Path(image_path), partner_id)
