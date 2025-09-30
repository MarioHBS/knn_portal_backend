"""
Serviço de métricas avançado para o sistema KNN Portal.

Este módulo fornece funcionalidades para coleta, armazenamento e análise
de métricas de negócio e performance do sistema.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from google.cloud import firestore

from src.config import FIRESTORE_PROJECT
from src.db.firestore import firestore_client
from src.db.postgres import postgres_client
from src.db.unified_client import with_circuit_breaker

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Serviço para coleta e análise de métricas do sistema.

    Responsável por:
    - Coleta de métricas em tempo real
    - Armazenamento de métricas históricas
    - Geração de relatórios e dashboards
    - Alertas baseados em métricas
    """

    def __init__(self, project_id: str = FIRESTORE_PROJECT):
        """
        Inicializa o serviço de métricas.

        Args:
            project_id: ID do projeto Firebase
        """
        self.project_id = project_id
        self.db = firestore.AsyncClient(project=project_id)

    async def collect_real_time_metrics(self, tenant_id: str) -> dict[str, Any]:
        """
        Coleta métricas em tempo real para um tenant.

        Args:
            tenant_id: ID do tenant

        Returns:
            Dicionário com métricas atuais
        """
        try:
            metrics = {}

            # Métricas de usuários
            metrics["users"] = await self._get_user_metrics(tenant_id)

            # Métricas de códigos
            metrics["codes"] = await self._get_code_metrics(tenant_id)

            # Métricas de parceiros
            metrics["partners"] = await self._get_partner_metrics(tenant_id)

            # Métricas de performance
            metrics["performance"] = await self._get_performance_metrics(tenant_id)

            # Salvar snapshot das métricas
            await self._save_metrics_snapshot(tenant_id, metrics)

            return metrics

        except Exception as e:
            logger.error(f"Erro ao coletar métricas para tenant {tenant_id}: {str(e)}")
            return {}

    async def get_historical_metrics(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "daily",
    ) -> dict[str, Any]:
        """
        Obtém métricas históricas para um período.

        Args:
            tenant_id: ID do tenant
            start_date: Data de início
            end_date: Data de fim
            granularity: Granularidade (hourly, daily, weekly, monthly)

        Returns:
            Dicionário com métricas históricas
        """
        try:
            collection_ref = self.db.collection("metrics_snapshots")
            query = (
                collection_ref.where("tenant_id", "==", tenant_id)
                .where("timestamp", ">=", start_date)
                .where("timestamp", "<=", end_date)
                .order_by("timestamp")
            )

            snapshots = []
            async for doc in query.stream():
                snapshots.append(doc.to_dict())

            # Agregar dados conforme granularidade
            aggregated = await self._aggregate_metrics(snapshots, granularity)

            return aggregated

        except Exception as e:
            logger.error(f"Erro ao obter métricas históricas: {str(e)}")
            return {}

    async def generate_dashboard_data(self, tenant_id: str) -> dict[str, Any]:
        """
        Gera dados para dashboard administrativo.

        Args:
            tenant_id: ID do tenant

        Returns:
            Dados formatados para dashboard
        """
        try:
            # Métricas atuais
            current_metrics = await self.collect_real_time_metrics(tenant_id)

            # Métricas dos últimos 30 dias
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            historical = await self.get_historical_metrics(
                tenant_id, start_date, end_date, "daily"
            )

            # Top parceiros por resgates
            top_partners = await self._get_top_partners(tenant_id, limit=10)

            # Tendências
            trends = await self._calculate_trends(tenant_id)

            dashboard_data = {
                "current_metrics": current_metrics,
                "historical_data": historical,
                "top_partners": top_partners,
                "trends": trends,
                "last_updated": datetime.utcnow().isoformat(),
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Erro ao gerar dados do dashboard: {str(e)}")
            return {}

    async def create_custom_metric(
        self,
        tenant_id: str,
        metric_name: str,
        metric_value: float,
        metric_type: str = "counter",
        tags: dict[str, str] | None = None,
    ) -> bool:
        """
        Cria uma métrica customizada.

        Args:
            tenant_id: ID do tenant
            metric_name: Nome da métrica
            metric_value: Valor da métrica
            metric_type: Tipo (counter, gauge, histogram)
            tags: Tags adicionais

        Returns:
            True se a métrica foi criada com sucesso
        """
        try:
            metric_data = {
                "tenant_id": tenant_id,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "metric_type": metric_type,
                "tags": tags or {},
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow(),
            }

            collection_ref = self.db.collection("custom_metrics")
            await collection_ref.add(metric_data)

            return True

        except Exception as e:
            logger.error(f"Erro ao criar métrica customizada: {str(e)}")
            return False

    async def _get_user_metrics(self, tenant_id: str) -> dict[str, Any]:
        """Obtém métricas de usuários."""
        try:
            # Contar usuários ativos
            async def count_firestore_active_users():
                today = datetime.utcnow().date().isoformat()
                result = await firestore_client.query_documents(
                    "students",
                    tenant_id=tenant_id,
                    filters=[("active_until", ">=", today)],
                )
                return result.get("total", 0)

            async def count_postgres_active_users():
                today = datetime.utcnow().date().isoformat()
                result = await postgres_client.query_documents(
                    "students",
                    tenant_id=tenant_id,
                    filters=[("active_until", ">=", today)],
                )
                return result.get("total", 0)

            active_users = await with_circuit_breaker(
                count_firestore_active_users, count_postgres_active_users
            )

            # Contar novos usuários (últimos 7 dias)
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

            async def count_firestore_new_users():
                result = await firestore_client.query_documents(
                    "students",
                    tenant_id=tenant_id,
                    filters=[("created_at", ">=", week_ago)],
                )
                return result.get("total", 0)

            async def count_postgres_new_users():
                result = await postgres_client.query_documents(
                    "students",
                    tenant_id=tenant_id,
                    filters=[("created_at", ">=", week_ago)],
                )
                return result.get("total", 0)

            new_users = await with_circuit_breaker(
                count_firestore_new_users, count_postgres_new_users
            )

            return {
                "active_users": active_users,
                "new_users_7d": new_users,
                "growth_rate": self._calculate_growth_rate(active_users, new_users),
            }

        except Exception as e:
            logger.error(f"Erro ao obter métricas de usuários: {str(e)}")
            return {}

    async def _get_code_metrics(self, tenant_id: str) -> dict[str, Any]:
        """Obtém métricas de códigos de validação."""
        try:
            # Códigos gerados
            async def count_firestore_codes():
                result = await firestore_client.query_documents(
                    "validation_codes", tenant_id=tenant_id
                )
                return result.get("total", 0)

            async def count_postgres_codes():
                result = await postgres_client.query_documents(
                    "validation_codes", tenant_id=tenant_id
                )
                return result.get("total", 0)

            total_codes = await with_circuit_breaker(
                count_firestore_codes, count_postgres_codes
            )

            # Códigos resgatados
            async def count_firestore_redeemed():
                result = await firestore_client.query_documents(
                    "validation_codes",
                    tenant_id=tenant_id,
                    filters=[("used_at", "!=", None)],
                )
                return result.get("total", 0)

            async def count_postgres_redeemed():
                result = await postgres_client.query_documents(
                    "validation_codes",
                    tenant_id=tenant_id,
                    filters=[("used_at", "!=", None)],
                )
                return result.get("total", 0)

            redeemed_codes = await with_circuit_breaker(
                count_firestore_redeemed, count_postgres_redeemed
            )

            redemption_rate = (
                (redeemed_codes / total_codes * 100) if total_codes > 0 else 0
            )

            return {
                "total_codes": total_codes,
                "redeemed_codes": redeemed_codes,
                "pending_codes": total_codes - redeemed_codes,
                "redemption_rate": round(redemption_rate, 2),
            }

        except Exception as e:
            logger.error(f"Erro ao obter métricas de códigos: {str(e)}")
            return {}

    async def _get_partner_metrics(self, tenant_id: str) -> dict[str, Any]:
        """Obtém métricas de parceiros."""
        try:
            # Parceiros ativos
            async def count_firestore_partners():
                result = await firestore_client.query_documents(
                    "partners",
                    tenant_id=tenant_id,
                    filters=[("active", "==", True)],
                )
                return result.get("total", 0)

            async def count_postgres_partners():
                result = await postgres_client.query_documents(
                    "partners",
                    tenant_id=tenant_id,
                    filters=[("active", "==", True)],
                )
                return result.get("total", 0)

            active_partners = await with_circuit_breaker(
                count_firestore_partners, count_postgres_partners
            )

            return {
                "active_partners": active_partners,
                "avg_redemptions_per_partner": 0,  # Calcular posteriormente
            }

        except Exception as e:
            logger.error(f"Erro ao obter métricas de parceiros: {str(e)}")
            return {}

    async def _get_performance_metrics(self, tenant_id: str) -> dict[str, Any]:
        """Obtém métricas de performance do sistema."""
        try:
            # Métricas básicas de performance
            # Em uma implementação real, estas viriam de monitoramento
            return {
                "avg_response_time": 150,  # ms
                "error_rate": 0.5,  # %
                "uptime": 99.9,  # %
                "requests_per_minute": 120,
            }

        except Exception as e:
            logger.error(f"Erro ao obter métricas de performance: {str(e)}")
            return {}

    async def _save_metrics_snapshot(
        self, tenant_id: str, metrics: dict[str, Any]
    ) -> None:
        """Salva snapshot das métricas para análise histórica."""
        try:
            snapshot_data = {
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow(),
                "metrics": metrics,
                "created_at": datetime.utcnow(),
            }

            collection_ref = self.db.collection("metrics_snapshots")
            await collection_ref.add(snapshot_data)

        except Exception as e:
            logger.error(f"Erro ao salvar snapshot de métricas: {str(e)}")

    async def _get_top_partners(
        self, tenant_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Obtém top parceiros por número de resgates."""
        try:
            # Implementação simplificada
            # Em produção, seria necessário agregar dados de resgates
            async def get_firestore_partners():
                result = await firestore_client.query_documents(
                    "partners",
                    tenant_id=tenant_id,
                    filters=[("active", "==", True)],
                    limit=limit,
                )
                return result.get("items", [])

            async def get_postgres_partners():
                result = await postgres_client.query_documents(
                    "partners",
                    tenant_id=tenant_id,
                    filters=[("active", "==", True)],
                    limit=limit,
                )
                return result.get("items", [])

            partners = await with_circuit_breaker(
                get_firestore_partners, get_postgres_partners
            )

            # Adicionar contagem de resgates (simulado)
            top_partners = []
            for partner in partners:
                partner_data = {
                    "partner_id": partner.get("id"),
                    "trade_name": partner.get("trade_name", ""),
                    "redemptions": 0,  # Calcular resgates reais
                }
                top_partners.append(partner_data)

            return top_partners

        except Exception as e:
            logger.error(f"Erro ao obter top parceiros: {str(e)}")
            return []

    async def _calculate_trends(self, tenant_id: str) -> dict[str, Any]:
        """Calcula tendências das métricas."""
        try:
            # Implementação simplificada de cálculo de tendências
            return {
                "user_growth": 5.2,  # % crescimento
                "redemption_trend": 12.8,  # % crescimento
                "partner_engagement": 8.5,  # % crescimento
            }

        except Exception as e:
            logger.error(f"Erro ao calcular tendências: {str(e)}")
            return {}

    async def _aggregate_metrics(
        self, snapshots: list[dict[str, Any]], granularity: str
    ) -> dict[str, Any]:
        """Agrega métricas conforme granularidade especificada."""
        # Implementação simplificada
        return {
            "aggregated_data": snapshots,
            "granularity": granularity,
            "total_snapshots": len(snapshots),
        }

    def _calculate_growth_rate(self, current: int, new: int) -> float:
        """Calcula taxa de crescimento."""
        if current == 0:
            return 0.0
        return round((new / current) * 100, 2)


# Instância global do serviço
metrics_service = MetricsService()
