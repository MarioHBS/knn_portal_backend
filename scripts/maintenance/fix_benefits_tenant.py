#!/usr/bin/env python3
"""
Script de manutenção para definir o tenant_id em documentos da coleção 'benefits'.

Funções:
- Atualiza o campo de nível de documento 'tenant_id' para o tenant informado.
- Opcionalmente, atualiza o campo 'system.tenant_id' de cada benefício (BNF_*) dentro do documento.

Por padrão, roda em modo dry-run (apenas exibe o que será alterado). Use --apply para executar as alterações.

Exemplos:
- Dry-run no documento PTN_T4L5678_TEC:
    python scripts/maintenance/fix_benefits_tenant.py --tenant knn-dev-tenant --doc-id PTN_T4L5678_TEC

- Aplicar ajustes em todos os documentos sem tenant_id, atualizando também cada benefício:
    python scripts/maintenance/fix_benefits_tenant.py --tenant knn-dev-tenant --apply --update-benefit-system
"""

import argparse
from typing import Any

from google.cloud import firestore

from src.utils import logger


def _is_benefit_key(key: str) -> bool:
    return isinstance(key, str) and key.startswith("BNF_")


def fix_benefits_tenant(
    tenant_id: str,
    doc_ids: list[str] | None = None,
    only_missing: bool = True,
    update_benefit_system: bool = False,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Define o tenant_id nos documentos da coleção 'benefits'.

    Args:
        tenant_id: Identificador do tenant a ser definido.
        doc_ids: Lista de IDs de documentos para filtrar (opcional). Se None, processa todos.
        only_missing: Se True, atualiza apenas quando o campo está ausente/vazio.
        update_benefit_system: Se True, também atualiza system.tenant_id em cada benefício (BNF_*).
        dry_run: Se True, não escreve no Firestore, apenas exibe o que seria feito.

    Returns:
        Resumo das operações realizadas/planejadas.
    """
    db = firestore.Client()
    benefits_ref = db.collection("benefits")

    processed = 0
    updated_doc_tenant = 0
    updated_benefit_tenant = 0
    skipped = 0

    def process_doc(doc_id: str, doc_data: dict[str, Any]):
        nonlocal processed, updated_doc_tenant, updated_benefit_tenant, skipped

        processed += 1
        current_doc_tenant = doc_data.get("tenant_id")
        updates: dict[str, Any] = {}

        # Decidir atualização de nível de documento
        need_update_doc = False
        if only_missing:
            need_update_doc = not bool(current_doc_tenant)
        else:
            need_update_doc = True

        if need_update_doc:
            updates["tenant_id"] = tenant_id

        # Atualização por benefício (BNF_*)
        if update_benefit_system:
            for key, value in doc_data.items():
                if not _is_benefit_key(key) or not isinstance(value, dict):
                    continue
                system = value.get("system", {}) if isinstance(value, dict) else {}
                current_b_tenant = system.get("tenant_id")

                need_update_benefit = False
                if only_missing:
                    need_update_benefit = not bool(current_b_tenant)
                else:
                    need_update_benefit = True

                if need_update_benefit:
                    # Campo aninhado: BNF_xxx.system.tenant_id
                    updates[f"{key}.system.tenant_id"] = tenant_id

        if updates:
            if dry_run:
                logger.info(
                    f"[fix_benefits_tenant] DRY-RUN | Doc={doc_id} | Updates={list(updates.keys())}"
                )
            else:
                doc_ref = benefits_ref.document(doc_id)
                doc_ref.update(updates)
                logger.info(
                    f"[fix_benefits_tenant] APPLIED | Doc={doc_id} | Updates={list(updates.keys())}"
                )

            if "tenant_id" in updates:
                updated_doc_tenant += 1
            # Contar quantos benefícios foram atualizados
            updated_benefit_tenant += sum(
                1 for k in updates if k.endswith(".system.tenant_id")
            )
        else:
            skipped += 1
            logger.debug(f"[fix_benefits_tenant] SKIP | Doc={doc_id} | sem alterações")

    # Processamento dos documentos
    if doc_ids:
        logger.info(
            f"[fix_benefits_tenant] Processando documentos específicos: {doc_ids} | tenant={tenant_id} | dry_run={dry_run} | only_missing={only_missing} | update_benefit_system={update_benefit_system}"
        )
        for doc_id in doc_ids:
            snap = benefits_ref.document(doc_id).get()
            if not snap.exists:
                logger.warning(
                    f"Documento {doc_id} não encontrado na coleção 'benefits'"
                )
                continue
            process_doc(doc_id, snap.to_dict())
    else:
        logger.info(
            f"[fix_benefits_tenant] Processando TODOS os documentos | tenant={tenant_id} | dry_run={dry_run} | only_missing={only_missing} | update_benefit_system={update_benefit_system}"
        )
        for snap in benefits_ref.stream():
            process_doc(snap.id, snap.to_dict())

    summary = {
        "processed": processed,
        "updated_doc_tenant": updated_doc_tenant,
        "updated_benefit_tenant": updated_benefit_tenant,
        "skipped": skipped,
        "dry_run": dry_run,
        "tenant_id": tenant_id,
        "doc_ids": doc_ids or [],
    }

    logger.info(
        "\n[fix_benefits_tenant] RESUMO: "
        + f"processados={processed} | docs_atualizados={updated_doc_tenant} | beneficios_atualizados={updated_benefit_tenant} | pulados={skipped} | dry_run={dry_run}"
    )

    return summary


def parse_args():
    parser = argparse.ArgumentParser(
        description="Corrige tenant_id na coleção 'benefits'"
    )
    parser.add_argument(
        "--tenant",
        required=True,
        help="Tenant ID a ser definido nos documentos (ex.: knn-dev-tenant)",
    )
    parser.add_argument(
        "--doc-id",
        help="ID do documento de parceiro na coleção 'benefits' (ex.: PTN_T4L5678_TEC). Use vírgula para múltiplos.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplicar alterações (por padrão é dry-run)",
    )
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Atualiza apenas quando o tenant_id estiver ausente (padrão)",
    )
    parser.add_argument(
        "--update-benefit-system",
        action="store_true",
        help="Também atualiza system.tenant_id dentro de cada benefício (BNF_*)",
    )

    # Por padrão, only_missing=True
    parser.set_defaults(only_missing=True)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    doc_ids = None
    if args.doc_id:
        doc_ids = [d.strip() for d in args.doc_id.split(",") if d.strip()]

    fix_benefits_tenant(
        tenant_id=args.tenant,
        doc_ids=doc_ids,
        only_missing=args.only_missing,
        update_benefit_system=args.update_benefit_system,
        dry_run=not args.apply,
    )
