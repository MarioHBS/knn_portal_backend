#!/usr/bin/env python3
"""
Script para testar se as referências de imagem dos parceiros
estão funcionando corretamente no Firestore e Firebase Storage.
"""

import os
import sys
from datetime import datetime

import requests

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError as e:
    print(f"❌ Erro ao importar Firebase Admin SDK: {e}")
    sys.exit(1)


def initialize_firebase():
    """Inicializa conexão com Firebase."""
    try:
        # Verifica se já foi inicializado
        try:
            app = firebase_admin.get_app()
            print("✅ Firebase já inicializado")
            return True
        except ValueError:
            pass

        # Inicializa Firebase
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {"projectId": "knn-benefits"})
        print("✅ Firebase inicializado com sucesso")
        return True

    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")
        return False


def test_image_url(url, partner_id):
    """Testa se uma URL de imagem está acessível."""
    try:
        response = requests.head(url, timeout=10)

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_length = response.headers.get("content-length", "0")

            if "image" in content_type:
                size_kb = (
                    round(int(content_length) / 1024, 2)
                    if content_length.isdigit()
                    else "N/A"
                )
                print(
                    f"   ✅ {partner_id}: Imagem acessível ({content_type}, {size_kb} KB)"
                )
                return True
            else:
                print(
                    f"   ⚠️  {partner_id}: URL acessível mas não é imagem ({content_type})"
                )
                return False
        else:
            print(f"   ❌ {partner_id}: HTTP {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print(f"   ❌ {partner_id}: Timeout na requisição")
        return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ {partner_id}: Erro na requisição - {e}")
        return False
    except Exception as e:
        print(f"   ❌ {partner_id}: Erro inesperado - {e}")
        return False


def test_partner_images():
    """Testa as imagens de todos os parceiros no Firestore."""

    if not initialize_firebase():
        return False

    try:
        db = firestore.client()
        partners_ref = db.collection("partners")

        print("\n🔍 Buscando parceiros no Firestore...")
        partners = list(partners_ref.stream())

        if not partners:
            print("❌ Nenhum parceiro encontrado no Firestore")
            return False

        print(f"📋 Encontrados {len(partners)} parceiro(s)\n")

        # Estatísticas
        total_partners = len(partners)
        partners_with_logo = 0
        partners_with_working_logo = 0
        partners_without_logo = 0

        print("=== TESTE DE IMAGENS DOS PARCEIROS ===")

        for partner_doc in partners:
            partner_id = partner_doc.id
            partner_data = partner_doc.to_dict()

            nome = partner_data.get("nome", "Nome não informado")
            logo_url = partner_data.get("logo_url")

            print(f"\n📋 {partner_id} - {nome}")

            if logo_url:
                partners_with_logo += 1
                print(f"   🔗 URL: {logo_url}")

                if test_image_url(logo_url, partner_id):
                    partners_with_working_logo += 1
            else:
                partners_without_logo += 1
                print("   ❌ Sem logo_url configurada")

        # Resumo final
        print("\n" + "=" * 50)
        print("=== RESUMO DOS TESTES ===")
        print(f"Total de parceiros: {total_partners}")
        print(f"Parceiros com logo_url: {partners_with_logo}")
        print(f"Parceiros com logo funcionando: {partners_with_working_logo}")
        print(f"Parceiros sem logo_url: {partners_without_logo}")

        if partners_with_logo > 0:
            success_rate = (partners_with_working_logo / partners_with_logo) * 100
            print(f"Taxa de sucesso: {success_rate:.1f}%")

        # Verifica se todos os uploads funcionaram
        if partners_with_working_logo == partners_with_logo and partners_with_logo > 0:
            print("\n✅ TODOS OS TESTES PASSARAM! Imagens funcionando corretamente.")
            return True
        elif partners_with_working_logo > 0:
            print("\n⚠️  ALGUNS TESTES FALHARAM. Verifique os erros acima.")
            return False
        else:
            print("\n❌ TODOS OS TESTES FALHARAM. Verifique a configuração.")
            return False

    except Exception as e:
        print(f"❌ Erro ao testar imagens: {e}")
        return False


def test_specific_partners():
    """Testa parceiros específicos que sabemos que foram processados."""

    expected_partners = [
        "PTN_A1E3018_AUT",
        "PTN_C0P4799_LIV",
        "PTN_C5C7628_TEC",
        "PTN_C8A3367_EDU",
        "PTN_E211033_EDU",
        "PTN_M365611_EDU",
    ]

    print("\n🎯 TESTE ESPECÍFICO DOS PARCEIROS PROCESSADOS")
    print("=" * 50)

    if not initialize_firebase():
        return False

    try:
        db = firestore.client()

        success_count = 0

        for partner_id in expected_partners:
            try:
                partner_ref = db.collection("partners").document(partner_id)
                partner_doc = partner_ref.get()

                if partner_doc.exists:
                    partner_data = partner_doc.to_dict()
                    logo_url = partner_data.get("logo_url")
                    nome = partner_data.get("nome", "Nome não informado")

                    print(f"\n📋 {partner_id} - {nome}")

                    if logo_url:
                        print(f"   🔗 URL: {logo_url}")
                        if test_image_url(logo_url, partner_id):
                            success_count += 1
                    else:
                        print("   ❌ Sem logo_url no Firestore")
                else:
                    print(f"\n❌ {partner_id}: Documento não encontrado no Firestore")

            except Exception as e:
                print(f"\n❌ {partner_id}: Erro ao verificar - {e}")

        print(
            f"\n📊 Resultado: {success_count}/{len(expected_partners)} parceiros com imagens funcionando"
        )

        if success_count == len(expected_partners):
            print(
                "✅ TESTE ESPECÍFICO PASSOU! Todos os parceiros processados têm imagens funcionando."
            )
            return True
        else:
            print(
                "⚠️  TESTE ESPECÍFICO PARCIALMENTE FALHOU. Alguns parceiros não têm imagens funcionando."
            )
            return False

    except Exception as e:
        print(f"❌ Erro no teste específico: {e}")
        return False


def generate_report(test_results):
    """Gera relatório dos testes."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"docs/teste_imagens_parceiros_{timestamp}.json"

    try:
        import json

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "image_references_validation",
            "results": test_results,
            "summary": {
                "total_tests": len(test_results.get("individual_tests", [])),
                "passed_tests": sum(
                    1
                    for test in test_results.get("individual_tests", [])
                    if test.get("success")
                ),
                "overall_success": test_results.get("overall_success", False),
            },
        }

        os.makedirs("docs", exist_ok=True)

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Relatório salvo em: {report_file}")

    except Exception as e:
        print(f"⚠️  Erro ao gerar relatório: {e}")


def main():
    """Função principal de teste."""
    print("🖼️  TESTE DE REFERÊNCIAS DE IMAGENS DOS PARCEIROS\n")

    # Executa teste geral
    print("1️⃣ EXECUTANDO TESTE GERAL...")
    general_success = test_partner_images()

    # Executa teste específico
    print("\n2️⃣ EXECUTANDO TESTE ESPECÍFICO...")
    specific_success = test_specific_partners()

    # Resultado final
    print("\n" + "=" * 60)
    print("=== RESULTADO FINAL ===")

    if general_success and specific_success:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("   - Imagens foram carregadas corretamente no Firebase Storage")
        print("   - URLs foram atualizadas no Firestore")
        print("   - Todas as imagens estão acessíveis")
        return True
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        if not general_success:
            print("   - Problemas no teste geral")
        if not specific_success:
            print("   - Problemas no teste específico")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
