#!/usr/bin/env python3
"""
Script para fazer upload das imagens processadas de parceiros para o Firebase Storage
e atualizar as referências no Firestore.
"""

import json
import os

# Importa configurações do Firebase
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from firebase_storage_config import (
    get_file_metadata,
    get_storage_path,
    validate_image_file,
)

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
except ImportError:
    print(
        "❌ Firebase Admin SDK não encontrado. Instale com: pip install firebase-admin"
    )
    sys.exit(1)


def initialize_firebase():
    """Inicializa o Firebase Admin SDK."""
    try:
        # Verifica se já foi inicializado
        firebase_admin.get_app()
        print("✅ Firebase já inicializado")
    except ValueError:
        # Inicializa com credenciais padrão
        try:
            # Tenta usar credenciais padrão com projeto específico
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(
                cred,
                {
                    "projectId": "knn-benefits",
                    "storageBucket": "knn-benefits.firebasestorage.app",
                },
            )
            print("✅ Firebase inicializado com credenciais padrão")
        except Exception as e:
            print(f"❌ Erro ao inicializar Firebase: {e}")
            print("💡 Certifique-se de ter configurado as credenciais do Firebase")
            return False

    return True


def upload_image_to_storage(
    local_path: Path, storage_path: str, partner_id: str = None
) -> dict[str, Any]:
    """Faz upload de uma imagem para o Firebase Storage."""
    try:
        # Valida o arquivo
        validation = validate_image_file(local_path)
        if not validation["valid"]:
            return {
                "success": False,
                "error": f"Arquivo inválido: {', '.join(validation['errors'])}",
            }

        # Obtém referência do Storage
        bucket = storage.bucket()
        blob = bucket.blob(storage_path)

        # Gera metadados
        metadata = get_file_metadata(local_path, partner_id)

        # Faz upload
        with open(local_path, "rb") as file_data:
            blob.upload_from_file(
                file_data, content_type=metadata.get("contentType", "image/png")
            )

        # Define metadados
        blob.metadata = metadata.get("customMetadata", {})
        blob.cache_control = metadata.get("cacheControl")
        blob.content_disposition = metadata.get("contentDisposition")
        blob.patch()

        # Torna público para leitura
        blob.make_public()

        return {
            "success": True,
            "storage_path": storage_path,
            "public_url": blob.public_url,
            "file_size": local_path.stat().st_size,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def extract_partner_id_from_filename(filename: str) -> str:
    """Extrai o ID do parceiro do nome do arquivo."""
    # Formato esperado: PTN_XXXXXXX_XXX.png
    if filename.startswith("PTN_"):
        parts = filename.split("_")
        if len(parts) >= 3:
            return f"PTN_{parts[1]}_{parts[2].split('.')[0]}"
    return filename.split(".")[0]


def update_partner_in_firestore(partner_id: str, image_url: str) -> dict[str, Any]:
    """Atualiza a referência da imagem no documento do parceiro no Firestore."""
    try:
        db = firestore.client()

        # Busca o documento do parceiro
        partner_ref = db.collection("partners").document(partner_id)
        partner_doc = partner_ref.get()

        if not partner_doc.exists:
            return {
                "success": False,
                "error": f"Parceiro {partner_id} não encontrado no Firestore",
            }

        # Atualiza com a URL da imagem
        partner_ref.update(
            {"logo_url": image_url, "logo_updated_at": datetime.now().isoformat()}
        )

        return {"success": True, "partner_id": partner_id, "updated_url": image_url}

    except Exception as e:
        return {"success": False, "error": str(e)}


def upload_all_processed_images():
    """Faz upload de todas as imagens processadas."""
    processed_dir = Path("statics/logos/processed")

    if not processed_dir.exists():
        print(f"❌ Diretório não encontrado: {processed_dir}")
        return

    # Inicializa Firebase
    if not initialize_firebase():
        return

    # Lista imagens processadas
    image_files = list(processed_dir.glob("*.png"))

    results = {
        "upload_date": datetime.now().isoformat(),
        "total_images": len(image_files),
        "uploads": [],
        "firestore_updates": [],
        "summary": {
            "successful_uploads": 0,
            "failed_uploads": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "total_size_uploaded": 0,
        },
    }

    print(f"Fazendo upload de {len(image_files)} imagens...\n")

    for image_file in sorted(image_files):
        print(f"📤 Uploading {image_file.name}...")

        # Extrai ID do parceiro
        partner_id = extract_partner_id_from_filename(image_file.name)

        # Define caminho no Storage
        storage_path = get_storage_path("partners", "logos") + image_file.name

        # Faz upload
        upload_result = upload_image_to_storage(image_file, storage_path, partner_id)
        upload_result["filename"] = image_file.name
        upload_result["partner_id"] = partner_id

        if upload_result["success"]:
            print(f"   ✅ Upload concluído: {upload_result['public_url']}")
            results["summary"]["successful_uploads"] += 1
            results["summary"]["total_size_uploaded"] += upload_result["file_size"]

            # Atualiza Firestore
            print(f"   📝 Atualizando Firestore para {partner_id}...")
            firestore_result = update_partner_in_firestore(
                partner_id, upload_result["public_url"]
            )
            firestore_result["partner_id"] = partner_id

            if firestore_result["success"]:
                print("   ✅ Firestore atualizado")
                results["summary"]["successful_updates"] += 1
            else:
                print(f"   ❌ Erro no Firestore: {firestore_result['error']}")
                results["summary"]["failed_updates"] += 1

            results["firestore_updates"].append(firestore_result)
        else:
            print(f"   ❌ Erro no upload: {upload_result['error']}")
            results["summary"]["failed_uploads"] += 1

        results["uploads"].append(upload_result)
        print()

    # Estatísticas finais
    print("\n=== RESUMO DO UPLOAD ===")
    print(f"Total de imagens: {results['total_images']}")
    print(f"Uploads bem-sucedidos: {results['summary']['successful_uploads']}")
    print(f"Uploads falharam: {results['summary']['failed_uploads']}")
    print(
        f"Atualizações Firestore bem-sucedidas: {results['summary']['successful_updates']}"
    )
    print(f"Atualizações Firestore falharam: {results['summary']['failed_updates']}")
    print(
        f"Tamanho total enviado: {results['summary']['total_size_uploaded'] / 1024:.2f} KB"
    )

    # Salva relatório
    report_path = (
        "docs/upload_imagens_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Relatório salvo em: {report_path}")
    return results


if __name__ == "__main__":
    upload_all_processed_images()
