"""
Módulo para integração com Firebase Analytics.

Este módulo fornece funcionalidades para rastrear eventos de negócio
e métricas de performance usando Firebase Analytics.
"""

import logging
from datetime import datetime
from typing import Any

import httpx
from google.cloud import firestore

from src.config import FIRESTORE_PROJECT

logger = logging.getLogger(__name__)


class FirebaseAnalytics:
    """
    Cliente para Firebase Analytics.

    Permite rastrear eventos customizados e métricas de negócio
    que podem ser visualizadas no console do Firebase.
    """

    def __init__(self, project_id: str = FIRESTORE_PROJECT):
        """
        Inicializa o cliente do Firebase Analytics.

        Args:
            project_id: ID do projeto Firebase
        """
        self.project_id = project_id
        self.db = firestore.AsyncClient(project=project_id)
        self._http_client = httpx.AsyncClient()

    async def track_event(
        self,
        event_name: str,
        parameters: dict[str, Any],
        user_id: str | None = None,
        tenant_id: str | None = None,
    ) -> bool:
        """
        Rastreia um evento customizado.

        Args:
            event_name: Nome do evento (ex: 'code_redeemed', 'partner_viewed')
            parameters: Parâmetros do evento
            user_id: ID do usuário (opcional)
            tenant_id: ID do tenant (opcional)

        Returns:
            True se o evento foi rastreado com sucesso
        """
        try:
            event_data = {
                "event_name": event_name,
                "timestamp": datetime.utcnow().isoformat(),
                "parameters": parameters,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "source": "backend_api",
            }

            # Salvar no Firestore para análise posterior
            await self._save_event_to_firestore(event_data)

            # Enviar para Firebase Analytics (se configurado)
            await self._send_to_firebase_analytics(event_data)

            return True

        except Exception as e:
            logger.error(f"Erro ao rastrear evento {event_name}: {str(e)}")
            return False

    async def track_business_metric(
        self,
        metric_name: str,
        value: float,
        tenant_id: str,
        additional_data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Rastreia uma métrica de negócio.

        Args:
            metric_name: Nome da métrica (ex: 'total_savings', 'redemption_rate')
            value: Valor da métrica
            tenant_id: ID do tenant
            additional_data: Dados adicionais (opcional)

        Returns:
            True se a métrica foi rastreada com sucesso
        """
        try:
            metric_data = {
                "metric_name": metric_name,
                "value": value,
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": tenant_id,
                "additional_data": additional_data or {},
            }

            # Salvar na coleção de métricas
            collection_ref = self.db.collection("analytics_metrics")
            await collection_ref.add(metric_data)

            return True

        except Exception as e:
            logger.error(f"Erro ao rastrear métrica {metric_name}: {str(e)}")
            return False

    async def get_analytics_summary(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """
        Obtém um resumo das métricas de analytics.

        Args:
            tenant_id: ID do tenant
            start_date: Data de início
            end_date: Data de fim

        Returns:
            Dicionário com resumo das métricas
        """
        try:
            # Buscar eventos no período
            events_ref = self.db.collection("analytics_events")
            events_query = (
                events_ref.where("tenant_id", "==", tenant_id)
                .where("timestamp", ">=", start_date.isoformat())
                .where("timestamp", "<=", end_date.isoformat())
            )

            events = []
            async for doc in events_query.stream():
                events.append(doc.to_dict())

            # Processar métricas
            summary = await self._process_events_summary(events)

            return summary

        except Exception as e:
            logger.error(f"Erro ao obter resumo de analytics: {str(e)}")
            return {}

    async def _save_event_to_firestore(self, event_data: dict[str, Any]) -> None:
        """Salva evento no Firestore para análise posterior."""
        try:
            collection_ref = self.db.collection("analytics_events")
            await collection_ref.add(event_data)
        except Exception as e:
            logger.error(f"Erro ao salvar evento no Firestore: {str(e)}")

    async def _send_to_firebase_analytics(self, event_data: dict[str, Any]) -> None:
        """
        Envia evento para Firebase Analytics via Measurement Protocol.

        Nota: Requer configuração adicional do Measurement Protocol
        """
        # Implementação futura do Measurement Protocol
        # Por enquanto, apenas log do evento
        logger.info(f"Evento Analytics: {event_data['event_name']}")

    async def _process_events_summary(
        self, events: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Processa lista de eventos e gera resumo."""
        summary = {
            "total_events": len(events),
            "event_types": {},
            "user_engagement": {},
            "business_metrics": {},
        }

        for event in events:
            event_name = event.get("event_name", "unknown")

            # Contar tipos de eventos
            if event_name not in summary["event_types"]:
                summary["event_types"][event_name] = 0
            summary["event_types"][event_name] += 1

            # Processar métricas específicas
            if event_name == "code_redeemed":
                if "redemptions" not in summary["business_metrics"]:
                    summary["business_metrics"]["redemptions"] = 0
                summary["business_metrics"]["redemptions"] += 1

            elif event_name == "partner_viewed":
                if "partner_views" not in summary["business_metrics"]:
                    summary["business_metrics"]["partner_views"] = 0
                summary["business_metrics"]["partner_views"] += 1

        return summary

    async def close(self) -> None:
        """Fecha conexões do cliente."""
        await self._http_client.aclose()


# Instância global do cliente
analytics_client = FirebaseAnalytics()


# Funções de conveniência para uso em endpoints
async def track_code_redemption(
    code_id: str,
    partner_id: str,
    user_id: str,
    tenant_id: str,
    value: float,
) -> None:
    """Rastreia resgate de código."""
    await analytics_client.track_event(
        "code_redeemed",
        {
            "code_id": code_id,
            "partner_id": partner_id,
            "value": value,
            "currency": "BRL",
        },
        user_id=user_id,
        tenant_id=tenant_id,
    )


async def track_partner_view(
    partner_id: str,
    user_id: str,
    tenant_id: str,
    user_role: str,
) -> None:
    """Rastreia visualização de parceiro."""
    await analytics_client.track_event(
        "partner_viewed",
        {
            "partner_id": partner_id,
            "user_role": user_role,
        },
        user_id=user_id,
        tenant_id=tenant_id,
    )


async def track_user_registration(
    user_id: str,
    tenant_id: str,
    user_role: str,
    registration_method: str = "email",
) -> None:
    """Rastreia registro de novo usuário."""
    await analytics_client.track_event(
        "user_registered",
        {
            "user_role": user_role,
            "registration_method": registration_method,
        },
        user_id=user_id,
        tenant_id=tenant_id,
    )
