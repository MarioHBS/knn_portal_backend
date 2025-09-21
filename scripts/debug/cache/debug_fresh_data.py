#!/usr/bin/env python3
"""
Script para limpar cache e verificar dados atuais do Firestore
Foca no tenant_id 'knn-dev-tenant' especificamente
"""

import gc
import time
from datetime import datetime

import jwt
import requests

from src.db.firestore import FirestoreClient, db, initialize_firestore_databases


def clear_cache_and_get_fresh_data():
    """Limpa cache e busca dados atuais do Firestore"""
    print("=== LIMPEZA DE CACHE E DADOS ATUAIS ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # 1. Forçar garbage collection para limpar cache
    print("1. Limpando cache Python...")
    gc.collect()
    time.sleep(1)

    # 2. Reinicializar cliente Firestore
    print("2. Reinicializando cliente Firestore...")
    initialize_firestore_databases()
    firestore_client = FirestoreClient()

    # 3. Fazer login real
    print("3. Fazendo login real...")
    login_url = "http://localhost:8080/v1/users/login"
    login_data = {
        "username": "aluno.teste@journeyclub.com.br",
        "password": "Tp654321"
    }

    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"Status do login: {login_response.status_code}")

        if login_response.status_code != 200:
            print(f"Erro no login: {login_response.text}")
            return

        token = login_response.json().get("access_token")
        print("✅ Login realizado com sucesso")

        # 4. Decodificar JWT
        print("\n4. Decodificando JWT...")
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        jwt_tenant_id = decoded_token.get("tenant")
        jwt_role = decoded_token.get("role")
        jwt_sub = decoded_token.get("sub")

        print(f"JWT tenant_id: '{jwt_tenant_id}'")
        print(f"JWT role: '{jwt_role}'")
        print(f"JWT sub: '{jwt_sub}'")

        # 5. Buscar dados ATUAIS do Firestore com foco no tenant específico
        print(f"\n5. Buscando dados ATUAIS do Firestore para tenant '{jwt_tenant_id}'...")

        # Buscar TODOS os parceiros primeiro
        all_partners = list(db.collection("partners").stream())
        print(f"Total de parceiros no Firestore: {len(all_partners)}")

        # Filtrar por tenant específico
        target_tenant_partners = []
        tenant_distribution = {}

        for partner_doc in all_partners:
            partner_data = partner_doc.to_dict()
            partner_tenant = partner_data.get("tenant_id", "N/A")

            # Contar distribuição
            if partner_tenant in tenant_distribution:
                tenant_distribution[partner_tenant] += 1
            else:
                tenant_distribution[partner_tenant] = 1

            # Filtrar por tenant específico
            if partner_tenant == jwt_tenant_id:
                target_tenant_partners.append({
                    "id": partner_doc.id,
                    "name": partner_data.get("name", "N/A"),
                    "tenant_id": partner_tenant,
                    "active": partner_data.get("active", False)
                })

        print("\nDistribuição de tenant_ids nos parceiros:")
        for tenant, count in sorted(tenant_distribution.items()):
            print(f"  '{tenant}': {count} parceiros")

        print(f"\nParceiros com tenant_id '{jwt_tenant_id}': {len(target_tenant_partners)}")

        if target_tenant_partners:
            print("\nDetalhes dos parceiros encontrados:")
            for partner in target_tenant_partners[:5]:  # Mostrar apenas os primeiros 5
                print(f"  - ID: {partner['id']}")
                print(f"    Nome: {partner['name']}")
                print(f"    Ativo: {partner['active']}")
                print()

        # 6. Testar endpoint com dados atuais
        print("6. Testando endpoint student/partners com dados atuais...")
        partners_url = "http://localhost:8080/v1/student/partners"
        headers = {"Authorization": f"Bearer {token}"}

        partners_response = requests.get(partners_url, headers=headers)
        print(f"Status do endpoint: {partners_response.status_code}")

        if partners_response.status_code == 200:
            partners_data = partners_response.json()
            print(f"Parceiros retornados pelo endpoint: {len(partners_data)}")

            if partners_data and isinstance(partners_data, list):
                print("\nPrimeiros parceiros do endpoint:")
                for partner in partners_data[:3]:
                    print(f"  - {partner.get('name', 'N/A')} (ID: {partner.get('id', 'N/A')})")
            elif partners_data:
                print(f"Formato inesperado de resposta: {type(partners_data)}")
                print(f"Conteúdo: {partners_data}")
        else:
            print(f"Erro no endpoint: {partners_response.text}")

        # 7. Análise final
        print("\n7. Análise Final:")
        print("=" * 50)

        if len(target_tenant_partners) == 0:
            print(f"❌ PROBLEMA: Nenhum parceiro encontrado com tenant_id '{jwt_tenant_id}'")
            print("   Possíveis causas:")
            print("   1. Dados não foram importados corretamente")
            print("   2. Tenant_id dos parceiros está diferente do esperado")
            print("   3. Cache ainda não foi limpo completamente")

            print("\n   Tenant_ids disponíveis no Firestore:")
            for tenant in sorted(tenant_distribution.keys()):
                if tenant != "N/A":
                    print(f"   - '{tenant}'")
        else:
            print(f"✅ Encontrados {len(target_tenant_partners)} parceiros com tenant_id '{jwt_tenant_id}'")

            if partners_response.status_code == 200:
                endpoint_count = len(partners_response.json())
                if endpoint_count == len(target_tenant_partners):
                    print("✅ Endpoint retorna a quantidade correta de parceiros")
                else:
                    print(f"⚠️  Discrepância: Firestore tem {len(target_tenant_partners)}, endpoint retorna {endpoint_count}")
            else:
                print("❌ Endpoint com problemas")

    except Exception as e:
        print(f"Erro durante execução: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clear_cache_and_get_fresh_data()
