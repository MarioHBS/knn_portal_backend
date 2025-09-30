"""
Utilitários para operações com parceiros.

Este módulo contém funções auxiliares para trabalhar com dados de parceiros,
incluindo obtenção de informações específicas necessárias para outras operações.
"""

from src.db import firestore_client, postgres_client, with_circuit_breaker


async def get_partner_name_by_entity_id(entity_id: str, tenant_id: str) -> str | None:
    """
    Obtém o nome comercial (trade_name) de um parceiro a partir do entity_id.

    Args:
        entity_id: ID da entidade (partner_id)
        tenant_id: ID do tenant para filtrar a consulta

    Returns:
        str: Nome comercial do parceiro ou None se não encontrado

    Raises:
        Exception: Em caso de erro na consulta ao banco de dados
    """
    try:
        # Definir funções para buscar no Firestore e PostgreSQL
        async def get_firestore_partner():
            return await firestore_client.get_document(
                "partners", entity_id, tenant_id=tenant_id
            )

        async def get_postgres_partner():
            return await postgres_client.get_document(
                "partners", entity_id, tenant_id=tenant_id
            )

        # Executar consulta com circuit breaker
        partner_result = await with_circuit_breaker(
            get_firestore_partner, get_postgres_partner
        )

        # Extrair dados do parceiro
        partner_data = partner_result.get("data") if partner_result else None

        if partner_data and partner_data.get("active", False):
            return partner_data.get("trade_name")

        return None

    except Exception as e:
        # Log do erro seria ideal aqui, mas mantendo simples por enquanto
        raise Exception(f"Erro ao obter nome do parceiro {entity_id}: {str(e)}") from e
