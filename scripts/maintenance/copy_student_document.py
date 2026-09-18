import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

# Garantir que o projeto raiz esteja no PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.db.firestore import firestore_client
from src.models import (
    StudentAddressDTO,
    StudentContactDTO,
    StudentFirestoreDTO,
    StudentGuardianDTO,
)


def transform_to_student_dto_payload(source: dict[str, Any]) -> dict[str, Any]:
    """
    Transforma diferentes formatos de documento de aluno em payload compatível com StudentDTO.
    Preenche campos faltantes com defaults seguros para ambiente de desenvolvimento.
    """
    # Campos base
    created_at = source.get("created_at")
    updated_at = source.get("updated_at")
    tenant_id = source.get("tenant_id")

    # Nome do aluno pode estar em diferentes campos
    name = source.get("name") or source.get("nome_aluno") or source.get("nome_completo")

    # active_until pode estar ausente em registros temporários
    active_until = source.get("active_until") or "2025-12-31"

    # Ocupação
    occupation = source.get("occupation") or (
        "Estudante" if source.get("status") in ("ativo", "inativo") else None
    )

    # Contato
    contact = source.get("contact")
    if not contact:
        contact = {
            "email": source.get("email"),
            "phone": source.get("telefone") or source.get("phone"),
        }

    # Endereço
    address = source.get("address")
    if not address:
        address = {
            "zip": source.get("cep"),
            "complement": source.get("complemento_aluno") or "",
            "neighborhood": source.get("bairro") or source.get("neighborhood") or "",
        }

    # Responsável
    guardian = source.get("guardian")
    if not guardian:
        guardian = {
            "email": source.get("email_responsavel") or "",
            "name": source.get("nome_responsavel") or "",
        }

    # Livro/curso
    book = source.get("book") or source.get("curso")

    payload = {
        "created_at": created_at,
        "updated_at": updated_at,
        "occupation": occupation,
        "tenant_id": tenant_id,
        "contact": contact,
        "address": address,
        "guardian": guardian,
        "active_until": active_until,
        "book": book,
        "name": name,
    }

    # Limpar None em subdocumentos usando DTOs auxiliares
    payload["contact"] = StudentContactDTO(**(payload["contact"] or {})).model_dump()
    payload["address"] = StudentAddressDTO(**(payload["address"] or {})).model_dump()
    payload["guardian"] = StudentGuardianDTO(**(payload["guardian"] or {})).model_dump()

    return payload


async def copy_student_document(source_id: str, target_id: str, tenant_id: str):
    # Ler documento de origem
    source = await firestore_client.get_document("students", source_id, tenant_id)
    if not source:
        print(
            f"❌ Documento de origem não encontrado: {source_id} (tenant={tenant_id})"
        )
        return

    # Transformar e validar com StudentDTO
    filtered = transform_to_student_dto_payload(source)
    try:
        dto = StudentFirestoreDTO(**filtered)
    except Exception as e:
        print(f"❌ Falha ao validar dados com StudentDTO: {e}")
        return

    payload = dto.model_dump(mode="json")
    # Garantir tenant_id no payload
    payload["tenant_id"] = tenant_id

    # Criar novo documento com ID alvo
    try:
        created = await firestore_client.create_document(
            "students", payload, doc_id=target_id
        )
        print(
            f"✅ Documento copiado com sucesso: {source_id} -> {target_id} (tenant={tenant_id})"
        )
        print(f"🆔 Novo ID: {created.get('id')}")
    except Exception as e:
        print(f"❌ Erro ao criar documento de destino: {e}")


def main():
    parser = argparse.ArgumentParser(description="Copiar documento da coleção students")
    parser.add_argument("--source_id", required=True, help="ID do documento de origem")
    parser.add_argument("--target_id", required=True, help="ID do novo documento")
    parser.add_argument(
        "--tenant_id",
        default="knn-dev-tenant",
        help="Tenant ID para filtrar/gravar",
    )
    args = parser.parse_args()

    asyncio.run(copy_student_document(args.source_id, args.target_id, args.tenant_id))


if __name__ == "__main__":
    main()
