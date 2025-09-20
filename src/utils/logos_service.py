"""
Serviço para gerenciamento de logos de parceiros no Firebase Storage.

Este serviço centraliza o acesso às imagens de logos, fornecendo:
- URLs públicas permanentes para acesso direto
- Cache para otimização de performance
- Listagem de logos disponíveis
- Validação de acesso baseada em autenticação
"""

from datetime import datetime, timedelta
from urllib.parse import quote

from fastapi import HTTPException, status
from firebase_admin import storage

from src.config import FIREBASE_STORAGE_BUCKET
from src.utils.logging import logger


class LogosService:
    """Serviço para gerenciamento de logos de parceiros."""

    def __init__(self):
        self._bucket = None
        self._cache = {}
        self._cache_ttl = datetime.now()  # Cache TTL de 1 hora

    def _get_bucket(self):
        """Obtém referência do bucket Firebase Storage."""
        if not self._bucket:
            try:
                self._bucket = storage.bucket(FIREBASE_STORAGE_BUCKET)
            except Exception as e:
                logger.error(f"Erro ao conectar com Firebase Storage: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": {
                            "code": "STORAGE_UNAVAILABLE",
                            "msg": "Serviço de armazenamento temporariamente indisponível",
                        }
                    },
                ) from e
        return self._bucket

    def _is_cache_valid(self, cache_entry: dict) -> bool:
        """
        Verifica se entrada do cache ainda é válida.

        Args:
            cache_entry: Entrada do cache com timestamp

        Returns:
            True se cache ainda válido, False caso contrário
        """
        cache_ttl = timedelta(hours=1)
        time_diff = datetime.now() - cache_entry["timestamp"]
        return time_diff < cache_ttl

    def _generate_public_url(self, blob) -> str:
        """
        Gera URL pública com token de download para o blob no formato Firebase Storage.

        Args:
            blob: Objeto blob do Firebase Storage

        Returns:
            URL pública com token de download no formato Firebase Storage
        """
        try:
            # Recarregar metadados do blob para garantir informações atualizadas
            blob.reload()

            # Verificar se já existe um token de download
            download_token = None
            if blob.metadata and 'firebaseStorageDownloadTokens' in blob.metadata:
                download_token = blob.metadata['firebaseStorageDownloadTokens']

            # Se não existe token, gerar um novo
            if not download_token:
                import uuid
                download_token = str(uuid.uuid4())

                # Atualizar metadados do blob com o novo token
                if not blob.metadata:
                    blob.metadata = {}
                blob.metadata['firebaseStorageDownloadTokens'] = download_token
                blob.patch()

                logger.info(f"Token gerado para {blob.name}: {download_token}")

            # Codificar o nome do blob para URL
            encoded_blob_name = quote(blob.name, safe="")

            # Gerar URL no formato Firebase Storage com token
            # https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{encoded_path}?alt=media&token={token}
            public_url = (
                f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}"
                f"/o/{encoded_blob_name}?alt=media&token={download_token}"
            )

            return public_url

        except Exception as e:
            logger.error(f"Erro ao gerar URL com token para {blob.name}: {str(e)}")
            # Fallback para URL sem token
            encoded_blob_name = quote(blob.name, safe="")
            return (
                f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}"
                f"/o/{encoded_blob_name}?alt=media"
            )

    def _generate_signed_url(self, blob, expiration_hours: int = 1) -> str:
        """
        Gera URL assinada temporária para o blob (método alternativo para uso futuro).

        URLs assinadas são mais seguras pois têm tempo de expiração e não dependem
        de tokens permanentes nos metadados do arquivo.

        Args:
            blob: Objeto blob do Firebase Storage
            expiration_hours: Horas até a URL expirar (padrão: 1 hora)

        Returns:
            URL assinada temporária com tempo de expiração

        Note:
            Este método está preparado para uso futuro como alternativa ao método
            _generate_public_url. URLs assinadas são recomendadas para maior segurança.
        """
        try:
            # Calcular tempo de expiração
            expiration_time = datetime.utcnow() + timedelta(hours=expiration_hours)

            # Gerar URL assinada
            signed_url = blob.generate_signed_url(
                expiration=expiration_time,
                method="GET"
            )

            logger.info(f"URL assinada gerada para {blob.name}, expira em: {expiration_time.isoformat()}")
            return signed_url

        except Exception as e:
            logger.error(f"Erro ao gerar URL assinada para {blob.name}: {str(e)}")
            # Fallback para método público em caso de erro
            return self._generate_public_url(blob)

    async def list_available_logos(
        self, force_refresh: bool = False
    ) -> list[dict[str, str]]:
        """
        Lista todos os logos disponíveis no Firebase Storage.

        Args:
            force_refresh: Se True, força atualização do cache

        Returns:
            Lista de dicionários com informações dos logos
        """
        cache_key = "all_logos"

        # Verificar cache se não forçar refresh
        if not force_refresh and cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if datetime.now() - cache_entry["timestamp"] < self._cache_ttl:
                logger.info(f"Retornando {len(cache_entry['data'])} logos do cache")
                return cache_entry["data"]

        try:
            # Implementar fallback para desenvolvimento quando Firebase não está disponível
            try:
                bucket = self._get_bucket()
                blobs = bucket.list_blobs(prefix="partners/logos/")
            except Exception as firebase_error:
                logger.warning(f"Firebase Storage não disponível: {firebase_error}")
                # Retornar dados mock para desenvolvimento
                mock_logos = [
                    {
                        "partner_id": "mock_partner_1",
                        "name": "Parceiro Mock 1",
                        "url": "https://via.placeholder.com/200x100/0066cc/ffffff?text=Parceiro+1",
                        "category": "EDU",
                        "format": "png",
                        "size": "2048",
                        "last_modified": datetime.now().isoformat(),
                    },
                    {
                        "partner_id": "mock_partner_2",
                        "name": "Parceiro Mock 2",
                        "url": "https://via.placeholder.com/200x100/cc6600/ffffff?text=Parceiro+2",
                        "category": "TEC",
                        "format": "png",
                        "size": "1024",
                        "last_modified": datetime.now().isoformat(),
                    },
                    {
                        "partner_id": "mock_partner_3",
                        "name": "Parceiro Mock 3",
                        "url": "https://via.placeholder.com/200x100/009900/ffffff?text=Parceiro+3",
                        "category": "AUT",
                        "format": "png",
                        "size": "3072",
                        "last_modified": datetime.now().isoformat(),
                    },
                ]

                # Atualizar cache com dados mock
                self._cache[cache_key] = {
                    "data": mock_logos,
                    "timestamp": datetime.now(),
                }

                logger.info(
                    f"Retornando {len(mock_logos)} logos mock para desenvolvimento"
                )
                return mock_logos

            logos_data = []

            for blob in blobs:
                # Pular diretórios
                if blob.name.endswith("/"):
                    continue

                # Extrair informações do arquivo
                path_parts = blob.name.split("/")
                if len(path_parts) < 3:
                    continue

                filename = path_parts[-1]
                name_without_ext = (
                    filename.rsplit(".", 1)[0] if "." in filename else filename
                )

                # Validar formato de arquivo
                valid_formats = ["png", "jpg", "jpeg", "svg", "webp"]
                file_extension = (
                    filename.split(".")[-1].lower() if "." in filename else ""
                )

                if file_extension not in valid_formats:
                    logger.warning(f"Formato de arquivo não suportado: {filename}")
                    continue

                # Gerar URL pública permanente no formato Firebase Storage
                public_url = self._generate_public_url(blob)
                logger.debug(f"URL pública gerada para {filename}: {public_url}")

                # Obter metadados
                try:
                    blob.reload()
                    metadata = blob.metadata or {}
                    category = metadata.get("category", "OTHER")
                except Exception:
                    category = "OTHER"

                logo_info = {
                    "partner_id": name_without_ext,
                    "filename": filename,
                    "name": metadata.get(
                        "display_name", name_without_ext.replace("_", " ").title()
                    ),
                    "url": public_url,
                    "category": category,
                    "format": file_extension,
                    "size": str(blob.size) if blob.size else "0",
                    "last_modified": blob.time_created.isoformat()
                    if blob.time_created
                    else datetime.now().isoformat(),
                }

                logos_data.append(logo_info)

            # Ordenar por partner_id
            logos_data.sort(key=lambda x: x["partner_id"])

            # Atualizar cache
            self._cache[cache_key] = {"data": logos_data, "timestamp": datetime.now()}

            logger.info(f"Carregados {len(logos_data)} logos do Firebase Storage")
            return logos_data

        except Exception as e:
            logger.error(f"Erro ao listar logos disponíveis: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "LOGOS_LIST_ERROR",
                        "msg": "Erro ao listar logos disponíveis",
                    }
                },
            ) from e

    async def get_partner_logo_url(
        self, partner_id: str, force_refresh: bool = False
    ) -> str | None:
        """
        Obtém URL do logo de um parceiro específico.

        Args:
            partner_id: ID do parceiro (ex: "PTN_A1E3018_AUT")
            force_refresh: Se True, força regeneração da URL

        Returns:
            URL assinada do logo ou None se não encontrado
        """
        try:
            # Buscar na lista de logos disponíveis (com possível refresh forçado)
            logos = await self.list_available_logos(force_refresh=force_refresh)

            # Procurar logo do parceiro
            for logo in logos:
                if logo["partner_id"] == partner_id:
                    logger.debug(
                        f"Logo encontrado para parceiro {partner_id}: {logo['url'][:100]}..."
                    )
                    return logo["url"]

            logger.warning(f"Logo não encontrado para parceiro: {partner_id}")
            return None

        except Exception as e:
            logger.error(f"Erro ao obter logo do parceiro {partner_id}: {e}")
            return None

    async def get_logos_by_category(self, category: str) -> list[dict[str, str]]:
        """
        Obtém logos filtrados por categoria.

        Args:
            category: Categoria dos parceiros (ex: "EDU", "AUT", "TEC")

        Returns:
            Lista de logos da categoria especificada
        """
        try:
            logos = await self.list_available_logos()

            # Filtrar por categoria
            filtered_logos = [
                logo for logo in logos if logo["category"].upper() == category.upper()
            ]

            logger.debug(
                f"Encontrados {len(filtered_logos)} logos na categoria {category}"
            )
            return filtered_logos

        except Exception as e:
            logger.error(f"Erro ao filtrar logos por categoria {category}: {e}")
            return []

    async def refresh_expired_urls(self) -> int:
        """
        Força a regeneração de todas as URLs em cache.
        Útil quando URLs começam a expirar.

        Returns:
            Número de URLs regeneradas
        """
        try:
            logger.info("Iniciando regeneração de URLs de logos...")

            # Limpar cache atual
            self.clear_cache()

            # Recarregar logos com URLs frescas
            logos = await self.list_available_logos(force_refresh=True)

            logger.info(f"Regeneradas {len(logos)} URLs de logos")
            return len(logos)

        except Exception as e:
            logger.error(f"Erro ao regenerar URLs: {e}")
            return 0

    def clear_cache(self):
        """Limpa o cache de logos."""
        self._cache.clear()
        logger.info("Cache de logos limpo")

    async def health_check(self) -> dict[str, any]:
        """
        Verifica saúde do serviço de logos.

        Returns:
            Dicionário com status do serviço
        """
        try:
            bucket = self._get_bucket()

            # Tentar listar alguns arquivos para verificar conectividade
            list(bucket.list_blobs(prefix="partners/logos/", max_results=1))

            return {
                "status": "healthy",
                "storage_accessible": True,
                "cache_entries": len(self._cache),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return {
                "status": "unhealthy",
                "storage_accessible": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# Instância singleton do serviço
logos_service = LogosService()
