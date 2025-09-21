#!/usr/bin/env python3
"""
Script para encontrar o bucket correto do Firebase Storage
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    import firebase_admin
    from firebase_admin import credentials, storage
    from google.cloud import storage as gcs
except ImportError as e:
    print(f"❌ Erro ao importar bibliotecas: {e}")
    sys.exit(1)

def test_bucket_names():
    """Testa diferentes nomes de bucket possíveis."""

    # Lista de buckets possíveis baseados no projeto
    possible_buckets = [
        "knn-benefits.appspot.com",
        "knn-benefits-default.appspot.com",
        "knn-benefits-firebase.appspot.com",
        "knn-benefits-storage.appspot.com",
        "knn-benefits-prod.appspot.com",
        "knn-benefits-dev.appspot.com"
    ]

    print("🔍 Testando buckets possíveis...\n")

    # Inicializa Firebase se ainda não foi
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': 'knn-benefits'
            })
        except Exception as e:
            print(f"❌ Erro ao inicializar Firebase: {e}")
            return []

    working_buckets = []

    for bucket_name in possible_buckets:
        try:
            print(f"Testando: {bucket_name}")

            # Tenta acessar o bucket
            bucket = storage.bucket(bucket_name)

            # Tenta listar arquivos (teste básico)
            try:
                blobs = list(bucket.list_blobs(max_results=1))
                print(f"  ✅ Bucket existe e é acessível ({len(blobs)} arquivo(s))")
                working_buckets.append(bucket_name)
            except Exception as list_error:
                # Bucket existe mas pode estar vazio ou ter problemas de permissão
                if "does not exist" in str(list_error).lower():
                    print("  ❌ Bucket não existe")
                else:
                    print(f"  ⚠️  Bucket existe mas erro na listagem: {list_error}")
                    working_buckets.append(bucket_name)

        except Exception as e:
            if "does not exist" in str(e).lower():
                print("  ❌ Bucket não existe")
            else:
                print(f"  ❌ Erro: {e}")

        print()

    return working_buckets

def list_project_buckets():
    """Lista todos os buckets do projeto usando Google Cloud Storage."""
    try:
        print("🗂️  Listando todos os buckets do projeto...\n")

        # Cria cliente do Google Cloud Storage
        client = gcs.Client(project='knn-benefits')

        buckets = list(client.list_buckets())

        if buckets:
            print(f"Encontrados {len(buckets)} bucket(s):")
            for bucket in buckets:
                print(f"  📦 {bucket.name}")

                # Tenta obter informações básicas
                try:
                    location = bucket.location
                    storage_class = bucket.storage_class
                    print(f"     Localização: {location}")
                    print(f"     Classe: {storage_class}")
                except Exception as e:
                    print(f"     Erro ao obter detalhes: {e}")
                print()

            return [bucket.name for bucket in buckets]
        else:
            print("❌ Nenhum bucket encontrado no projeto")
            return []

    except Exception as e:
        print(f"❌ Erro ao listar buckets: {e}")
        return []

def main():
    """Função principal."""
    print("🔥 BUSCANDO BUCKET CORRETO DO FIREBASE STORAGE\n")

    # Primeiro, tenta listar todos os buckets do projeto
    project_buckets = list_project_buckets()

    # Depois, testa buckets específicos
    working_buckets = test_bucket_names()

    print("=== RESULTADO FINAL ===")

    if project_buckets:
        print("📦 Buckets encontrados no projeto:")
        for bucket in project_buckets:
            print(f"   - {bucket}")

    if working_buckets:
        print("\n✅ Buckets acessíveis para Firebase:")
        for bucket in working_buckets:
            print(f"   - {bucket}")

        print(f"\n💡 Recomendação: Use '{working_buckets[0]}' no seu script")
    else:
        print("\n❌ Nenhum bucket acessível encontrado")
        print("\n💡 SOLUÇÕES POSSÍVEIS:")
        print("1. Verifique se o projeto 'knn-benefits' está correto")
        print("2. Crie um bucket no Firebase Console")
        print("3. Verifique as permissões de acesso")
        print("4. Configure as credenciais corretamente")

if __name__ == "__main__":
    main()
