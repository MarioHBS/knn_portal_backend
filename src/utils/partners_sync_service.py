"""
Serviço para sincronização automática de URLs de logos na coleção partners.

Este módulo fornece funcionalidades para manter as URLs de logos dos parceiros
atualizadas, garantindo que sempre apontem para as imagens corretas no Firebase Storage.
"""

from datetime import datetime, timedelta
from typing import Any

from src.db import firestore_client
from src.utils.logging import logger
from src.utils.logos_service import logos_service


class PartnersSyncService:
    """
    Serviço para sincronização automática de URLs de logos na coleção partners.

    Este serviço mantém as URLs de logos dos parceiros atualizadas,
    garantindo que sempre apontem para as imagens corretas no Firebase Storage.
    """

    def __init__(self):
        """Inicializa o serviço de sincronização."""
        self.batch_size = 50
        self.max_retries = 3

    async def sync_all_partner_logos(
        self,
        force_update: bool = False,
        batch_size: int | None = None,
    ) -> dict[str, Any]:
        """
        Sincroniza URLs de logos para todos os parceiros.

        Args:
            force_update: Se True, atualiza todos os logos independente da data
            batch_size: Tamanho do lote para processamento (padrão: 50)

        Returns:
            Dicionário com estatísticas da sincronização
        """
        try:
            batch_size = batch_size or self.batch_size
            stats = {
                "total_processed": 0,
                "updated": 0,
                "errors": 0,
                "skipped": 0,
                "start_time": datetime.now(),
            }

            logger.info(
                "sync_all_started",
                force_update=force_update,
                batch_size=batch_size,
            )

            # Buscar todos os parceiros
            partners_ref = firestore_client.collection("partners")
            partners_docs = partners_ref.stream()

            # Processar em lotes
            batch = []
            for doc in partners_docs:
                batch.append(doc)
                if len(batch) >= batch_size:
                    batch_stats = await self._process_partner_batch(
                        batch, force_update
                    )
                    self._update_stats(stats, batch_stats)
                    batch = []

            # Processar lote restante
            if batch:
                batch_stats = await self._process_partner_batch(batch, force_update)
                self._update_stats(stats, batch_stats)

            stats["end_time"] = datetime.now()
            stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()

            logger.info("sync_all_completed", stats=stats)
            return stats

        except Exception as e:
            logger.error("sync_all_failed", error=str(e))
            raise

    async def sync_partner_logo(
        self,
        partner_id: str,
        force_update: bool = False,
    ) -> dict[str, Any]:
        """
        Sincroniza URL do logo para um parceiro específico.

        Args:
            partner_id: ID do parceiro
            force_update: Se True, atualiza independente da data

        Returns:
            Dicionário com resultado da sincronização
        """
        try:
            logger.info(
                "sync_partner_started",
                partner_id=partner_id,
                force_update=force_update,
            )

            # Buscar parceiro
            partner_ref = firestore_client.collection("partners").document(partner_id)
            partner_doc = partner_ref.get()

            if not partner_doc.exists:
                raise ValueError(f"Parceiro {partner_id} não encontrado")

            partner_data = partner_doc.to_dict()

            # Buscar URL do logo
            logo_url = logos_service.get_partner_logo_url(
                partner_id, use_placeholder=True
            )

            current_logo_url = partner_data.get("logo_url")
            logo_updated_at = partner_data.get("logo_updated_at")

            # Verificar se precisa atualizar
            needs_update = force_update or current_logo_url != logo_url

            if not needs_update and logo_updated_at:
                # Verificar se foi atualizado nas últimas 24h
                try:
                    last_update = datetime.fromisoformat(logo_updated_at.replace("Z", "+00:00"))
                    if datetime.now() - last_update < timedelta(hours=24):
                        logger.info(
                            "sync_partner_skipped",
                            partner_id=partner_id,
                            reason="recently_updated",
                        )
                        return {
                            "partner_id": partner_id,
                            "action": "skipped",
                            "reason": "recently_updated",
                        }
                except (ValueError, AttributeError):
                    # Se não conseguir parsear a data, força atualização
                    needs_update = True

            if needs_update:
                # Atualizar logo_url
                update_data = {
                    "logo_url": logo_url,
                    "logo_updated_at": datetime.now().isoformat(),
                }

                partner_ref.update(update_data)

                logger.info(
                    "sync_partner_updated",
                    partner_id=partner_id,
                    old_url=current_logo_url,
                    new_url=logo_url,
                )

                return {
                    "partner_id": partner_id,
                    "action": "updated",
                    "old_url": current_logo_url,
                    "new_url": logo_url,
                }
            else:
                logger.info(
                    "sync_partner_skipped",
                    partner_id=partner_id,
                    reason="no_changes",
                )
                return {
                    "partner_id": partner_id,
                    "action": "skipped",
                    "reason": "no_changes",
                }

        except Exception as e:
            logger.error(
                "sync_partner_failed",
                partner_id=partner_id,
                error=str(e),
            )
            raise

    async def check_outdated_logos(
        self,
        hours_threshold: int = 24,
    ) -> dict[str, Any]:
        """
        Verifica parceiros com logos desatualizados.

        Args:
            hours_threshold: Limite em horas para considerar desatualizado

        Returns:
            Lista de parceiros com logos desatualizados
        """
        try:
            logger.info(
                "check_outdated_started",
                hours_threshold=hours_threshold,
            )

            threshold_time = datetime.now() - timedelta(hours=hours_threshold)
            outdated_partners = []

            # Buscar todos os parceiros
            partners_ref = firestore_client.collection("partners")
            partners_docs = partners_ref.stream()

            for doc in partners_docs:
                partner_data = doc.to_dict()
                partner_id = doc.id

                logo_updated_at = partner_data.get("logo_updated_at")

                # Se não tem data de atualização ou está desatualizado
                if not logo_updated_at:
                    outdated_partners.append({
                        "partner_id": partner_id,
                        "name": partner_data.get("name", "N/A"),
                        "reason": "no_update_date",
                        "logo_url": partner_data.get("logo_url"),
                    })
                else:
                    try:
                        last_update = datetime.fromisoformat(
                            logo_updated_at.replace("Z", "+00:00")
                        )
                        if last_update < threshold_time:
                            outdated_partners.append({
                                "partner_id": partner_id,
                                "name": partner_data.get("name", "N/A"),
                                "reason": "outdated",
                                "last_update": logo_updated_at,
                                "logo_url": partner_data.get("logo_url"),
                            })
                    except (ValueError, AttributeError):
                        outdated_partners.append({
                            "partner_id": partner_id,
                            "name": partner_data.get("name", "N/A"),
                            "reason": "invalid_date",
                            "logo_url": partner_data.get("logo_url"),
                        })

            result = {
                "threshold_hours": hours_threshold,
                "total_outdated": len(outdated_partners),
                "outdated_partners": outdated_partners,
                "checked_at": datetime.now().isoformat(),
            }

            logger.info(
                "check_outdated_completed",
                total_outdated=len(outdated_partners),
            )

            return result

        except Exception as e:
            logger.error("check_outdated_failed", error=str(e))
            raise

    async def _process_partner_batch(
        self,
        batch: list,
        force_update: bool = False,
    ) -> dict[str, int]:
        """
        Processa um lote de parceiros.

        Args:
            batch: Lista de documentos de parceiros
            force_update: Se True, força atualização

        Returns:
            Estatísticas do processamento do lote
        """
        stats = {"processed": 0, "updated": 0, "errors": 0, "skipped": 0}

        for doc in batch:
            try:
                partner_id = doc.id
                partner_data = doc.to_dict()

                # Buscar URL do logo
                logo_url = logos_service.get_partner_logo_url(
                    partner_id, use_placeholder=True
                )

                current_logo_url = partner_data.get("logo_url")
                logo_updated_at = partner_data.get("logo_updated_at")

                # Verificar se precisa atualizar
                needs_update = force_update or current_logo_url != logo_url

                # Se não é force_update, verificar se está desatualizado
                if not force_update and current_logo_url == logo_url and logo_updated_at:
                    try:
                        # Verificar se foi atualizado nas últimas 24h
                        last_update = datetime.fromisoformat(
                            logo_updated_at.replace("Z", "+00:00")
                        )
                        if datetime.now() - last_update < timedelta(hours=24):
                            stats["skipped"] += 1
                            stats["processed"] += 1
                            continue
                    except (ValueError, AttributeError):
                        # Se não conseguir parsear a data, força atualização
                        needs_update = True

                if needs_update:
                    # Atualizar logo_url
                    update_data = {
                        "logo_url": logo_url,
                        "logo_updated_at": datetime.now().isoformat(),
                    }

                    doc.reference.update(update_data)
                    stats["updated"] += 1

                    logger.debug(
                        "partner_logo_updated",
                        partner_id=partner_id,
                        old_url=current_logo_url,
                        new_url=logo_url,
                    )
                else:
                    stats["skipped"] += 1

                stats["processed"] += 1

            except Exception as e:
                stats["errors"] += 1
                stats["processed"] += 1
                logger.error(
                    "partner_sync_error",
                    partner_id=doc.id,
                    error=str(e),
                )

        return stats

    def _update_stats(self, main_stats: dict, batch_stats: dict) -> None:
        """Atualiza estatísticas principais com dados do lote."""
        main_stats["total_processed"] += batch_stats["processed"]
        main_stats["updated"] += batch_stats["updated"]
        main_stats["errors"] += batch_stats["errors"]
        main_stats["skipped"] += batch_stats["skipped"]


# Instância singleton do serviço
partners_sync_service = PartnersSyncService()
