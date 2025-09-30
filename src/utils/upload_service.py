"""
Serviço de upload administrativo para logos de parceiros.

Este módulo fornece funcionalidades para upload seguro de logos com validação
de formato, nomenclatura e integração com Firebase Storage.
"""

import re
from io import BytesIO

from fastapi import HTTPException, UploadFile
from PIL import Image

from src.db import storage_client
from src.utils.logging import logger


class UploadService:
    """Serviço para gerenciar uploads administrativos de logos."""

    def __init__(self):
        """Inicializa o serviço de upload."""
        from src.config import FIREBASE_STORAGE_BUCKET

        self.bucket = storage_client.bucket(FIREBASE_STORAGE_BUCKET)
        self.allowed_formats = {"png", "jpg", "jpeg", "webp", "svg"}
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        self.min_dimensions = (100, 100)  # Mínimo 100x100 pixels
        self.max_dimensions = (2000, 2000)  # Máximo 2000x2000 pixels

    async def upload_partner_logo(
        self, file: UploadFile, partner_id: str, category: str, overwrite: bool = False
    ) -> dict[str, str]:
        """
        Faz upload de logo de parceiro com validação completa.

        Args:
            file: Arquivo de upload
            partner_id: ID do parceiro
            category: Categoria do parceiro (EDU, SAU, etc.)
            overwrite: Se deve sobrescrever arquivo existente

        Returns:
            Dict com informações do upload

        Raises:
            HTTPException: Em caso de erro de validação ou upload
        """
        try:
            # Validar arquivo
            await self._validate_file(file)

            # Validar nomenclatura
            filename = self._generate_filename(partner_id, category, file.filename)

            # Verificar se arquivo já existe
            if not overwrite and await self._file_exists(filename):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": {
                            "code": "FILE_EXISTS",
                            "msg": f"Logo já existe para o parceiro {partner_id}. Use overwrite=true para substituir.",
                        }
                    },
                )

            # Processar imagem se necessário
            processed_content = await self._process_image(file)

            # Fazer upload
            blob_name = f"partners/logos/{filename}"
            blob = self.bucket.blob(blob_name)

            # Upload do arquivo
            blob.upload_from_string(processed_content, content_type=file.content_type)

            # Tornar público
            blob.make_public()

            # Obter URL pública
            public_url = blob.public_url

            logger.info(
                f"Upload concluído para parceiro {partner_id}",
                extra={
                    "partner_id": partner_id,
                    "filename": filename,
                    "size": len(processed_content),
                    "url": public_url,
                },
            )

            return {
                "success": True,
                "partner_id": partner_id,
                "filename": filename,
                "url": public_url,
                "size": len(processed_content),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro no upload: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {"code": "UPLOAD_ERROR", "msg": "Erro interno no upload"}
                },
            ) from e

    async def _validate_file(self, file: UploadFile) -> None:
        """
        Valida o arquivo de upload.

        Args:
            file: Arquivo para validação

        Raises:
            HTTPException: Se arquivo inválido
        """
        # Verificar se arquivo foi enviado
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {"code": "NO_FILE", "msg": "Nenhum arquivo foi enviado"}
                },
            )

        # Verificar extensão
        file_ext = file.filename.lower().split(".")[-1]
        if file_ext not in self.allowed_formats:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_FORMAT",
                        "msg": f"Formato não suportado. Use: {', '.join(self.allowed_formats)}",
                    }
                },
            )

        # Verificar tamanho
        content = await file.read()
        await file.seek(0)  # Reset para próximas leituras

        if len(content) > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "FILE_TOO_LARGE",
                        "msg": f"Arquivo muito grande. Máximo: {self.max_file_size // (1024*1024)}MB",
                    }
                },
            )

        # Verificar dimensões (apenas para imagens não-SVG)
        if file_ext != "svg":
            try:
                image = Image.open(BytesIO(content))
                width, height = image.size

                if width < self.min_dimensions[0] or height < self.min_dimensions[1]:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": {
                                "code": "IMAGE_TOO_SMALL",
                                "msg": f"Imagem muito pequena. Mínimo: {self.min_dimensions[0]}x{self.min_dimensions[1]}px",
                            }
                        },
                    )

                if width > self.max_dimensions[0] or height > self.max_dimensions[1]:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": {
                                "code": "IMAGE_TOO_LARGE",
                                "msg": f"Imagem muito grande. Máximo: {self.max_dimensions[0]}x{self.max_dimensions[1]}px",
                            }
                        },
                    )

            except Exception as e:
                if isinstance(e, HTTPException):
                    raise
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": {
                            "code": "INVALID_IMAGE",
                            "msg": "Arquivo de imagem inválido",
                        }
                    },
                ) from e

    def _generate_filename(
        self, partner_id: str, category: str, original_filename: str
    ) -> str:
        """
        Gera nome padronizado para o arquivo.

        Args:
            partner_id: ID do parceiro
            category: Categoria do parceiro
            original_filename: Nome original do arquivo

        Returns:
            Nome padronizado do arquivo

        Raises:
            HTTPException: Se dados inválidos
        """
        # Validar partner_id
        if not re.match(r"^[A-Z0-9_]+$", partner_id):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_PARTNER_ID",
                        "msg": "Partner ID deve conter apenas letras maiúsculas, números e underscore",
                    }
                },
            )

        # Validar categoria
        valid_categories = {"EDU", "SAU", "ALI", "TUR", "SER", "PAP", "OUT"}
        if category.upper() not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_CATEGORY",
                        "msg": f"Categoria inválida. Use: {', '.join(valid_categories)}",
                    }
                },
            )

        # Obter extensão
        file_ext = original_filename.lower().split(".")[-1]

        # Gerar nome padronizado: PTN_{partner_id}_{category}.{ext}
        return f"PTN_{partner_id}_{category.upper()}.{file_ext}"

    async def _file_exists(self, filename: str) -> bool:
        """
        Verifica se arquivo já existe no storage.

        Args:
            filename: Nome do arquivo

        Returns:
            True se arquivo existe
        """
        try:
            blob_name = f"partners/logos/{filename}"
            blob = self.bucket.blob(blob_name)
            return blob.exists()
        except Exception:
            return False

    async def _process_image(self, file: UploadFile) -> bytes:
        """
        Processa imagem para otimização.

        Args:
            file: Arquivo de imagem

        Returns:
            Conteúdo processado da imagem
        """
        content = await file.read()

        # Para SVG, retornar sem processamento
        if file.filename.lower().endswith(".svg"):
            return content

        try:
            # Otimizar imagem
            image = Image.open(BytesIO(content))

            # Converter para RGB se necessário
            if image.mode in ("RGBA", "P"):
                # Manter transparência para PNG
                if file.content_type == "image/png":
                    image = image.convert("RGBA")
                else:
                    image = image.convert("RGB")

            # Salvar otimizado
            output = BytesIO()
            format_map = {
                "image/jpeg": "JPEG",
                "image/jpg": "JPEG",
                "image/png": "PNG",
                "image/webp": "WEBP",
            }

            save_format = format_map.get(file.content_type, "PNG")

            # Configurações de qualidade
            save_kwargs = {"format": save_format}
            if save_format == "JPEG":
                save_kwargs["quality"] = 85
                save_kwargs["optimize"] = True
            elif save_format == "PNG":
                save_kwargs["optimize"] = True
            elif save_format == "WEBP":
                save_kwargs["quality"] = 85
                save_kwargs["optimize"] = True

            image.save(output, **save_kwargs)
            return output.getvalue()

        except Exception as e:
            logger.warning(f"Erro ao processar imagem, usando original: {e}")
            return content

    # TODO: melhorar a lógica da exclusão, nome de arquivo errada
    async def delete_partner_logo(
        self, partner_id: str, category: str
    ) -> dict[str, str]:
        """
        Remove logo de parceiro do storage.

        Args:
            partner_id: ID do parceiro
            category: Categoria do parceiro

        Returns:
            Dict com resultado da operação
        """
        try:
            # Gerar nome do arquivo
            filename = (
                f"PTN_{partner_id}_{category.upper()}.png"  # Assumir PNG como padrão
            )

            # Tentar diferentes extensões
            extensions = ["png", "jpg", "jpeg", "webp", "svg"]
            deleted = False

            for ext in extensions:
                test_filename = f"PTN_{partner_id}_{category.upper()}.{ext}"
                blob_name = f"partners/logos/{test_filename}"
                blob = self.bucket.blob(blob_name)

                if blob.exists():
                    blob.delete()
                    deleted = True
                    filename = test_filename
                    break

            if not deleted:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": {
                            "code": "FILE_NOT_FOUND",
                            "msg": f"Logo não encontrado para parceiro {partner_id}",
                        }
                    },
                )

            logger.info(f"Logo removido: {filename}")

            return {
                "success": True,
                "partner_id": partner_id,
                "filename": filename,
                "message": "Logo removido com sucesso",
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao remover logo: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": "DELETE_ERROR",
                        "msg": "Erro interno ao remover logo",
                    }
                },
            ) from e


# Instância singleton do serviço
upload_service = UploadService()
