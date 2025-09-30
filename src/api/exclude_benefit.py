from datetime import UTC, datetime

from google.api_core.exceptions import NotFound
from google.cloud import firestore

db = firestore.Client()


def delete_benefit_hard(partner_id: str, benefit_id: str) -> dict | None:
    """
    Hard delete: remove a chave `benefit_id` do documento /benefits/{partner_id}.
    Retorna os dados removidos ou None se não existia.
    """
    doc_ref = db.collection("benefits").document(partner_id)

    @firestore.transactional
    def _txn(txn):
        snap = doc_ref.get(transaction=txn)
        if not snap.exists:
            raise NotFound(f"Documento do parceiro '{partner_id}' não encontrado.")
        data = snap.to_dict() or {}
        if benefit_id not in data:
            return None
        removed = data[benefit_id]
        # Remove a chave do documento (campo raiz com nome do benefit_id)
        txn.update(doc_ref, {benefit_id: firestore.DELETE_FIELD})
        return removed

    return _txn(db.transaction())


def delete_benefit_soft(partner_id: str, benefit_id: str) -> dict | None:
    """
    Soft delete: move o objeto do benefício para a subcoleção
    /benefits/{partner_id}/deleted_benefits/{benefit_id}, acrescentando metadata.
    Retorna o objeto salvo (com metadata) ou None se não existia.
    """
    doc_ref = db.collection("benefits").document(partner_id)
    deleted_col = doc_ref.collection("deleted_benefits")
    deleted_doc_ref = deleted_col.document(benefit_id)

    @firestore.transactional
    def _txn(txn):
        snap = doc_ref.get(transaction=txn)
        if not snap.exists:
            raise NotFound(f"Documento do parceiro '{partner_id}' não encontrado.")
        data = snap.to_dict() or {}
        if benefit_id not in data:
            return None
        value = data[benefit_id]
        # enrich with deletion metadata
        value_with_meta = {
            **(value if isinstance(value, dict) else {"value": value}),
            "_deleted_at": datetime.now(UTC).isoformat(),
        }
        # criar documento na subcoleção e remover do map raiz
        txn.set(deleted_doc_ref, value_with_meta)
        txn.update(doc_ref, {benefit_id: firestore.DELETE_FIELD})
        return value_with_meta

    return _txn(db.transaction())
