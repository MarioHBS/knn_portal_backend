#!/usr/bin/env python3
"""
Script para deploy das regras de segurança do Firestore para o projeto knn-benefits.

Este script facilita o processo de deploy das regras de segurança,
validação e configuração de índices para o banco de dados de produção.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Executa um comando e retorna o resultado."""
    print(f"\n🔄 {description}...")
    print(f"Executando: {command}")

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
        print(f"✅ {description} - Sucesso")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erro")
        print(f"Erro: {e.stderr}")
        return False


def check_prerequisites():
    """Verifica se os pré-requisitos estão instalados."""
    print("🔍 Verificando pré-requisitos...")

    # Verificar se Firebase CLI está instalado
    try:
        result = subprocess.run(
            "firebase --version", shell=True, capture_output=True, text=True, check=True
        )
        print(f"✅ Firebase CLI instalado: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("❌ Firebase CLI não encontrado")
        print("Instale com: npm install -g firebase-tools")
        return False

    # Verificar se os arquivos de regras existem
    rules_file = Path("firestore_rules_production.rules")
    if not rules_file.exists():
        print(f"❌ Arquivo de regras não encontrado: {rules_file}")
        return False
    print(f"✅ Arquivo de regras encontrado: {rules_file}")

    # Verificar se o arquivo de índices existe
    indexes_file = Path("firestore.indexes.json")
    if not indexes_file.exists():
        print(f"❌ Arquivo de índices não encontrado: {indexes_file}")
        return False
    print(f"✅ Arquivo de índices encontrado: {indexes_file}")

    return True


def login_firebase():
    """Faz login no Firebase se necessário."""
    print("\n🔐 Verificando autenticação Firebase...")

    # Verificar se já está logado
    try:
        result = subprocess.run(
            "firebase projects:list",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
        if "knn-benefits" in result.stdout:
            print("✅ Já autenticado e projeto knn-benefits encontrado")
            return True
        else:
            print("⚠️ Autenticado mas projeto knn-benefits não encontrado")
            print("Verifique se você tem acesso ao projeto knn-benefits")
            return False
    except subprocess.CalledProcessError:
        print("❌ Não autenticado")
        print("Execute: firebase login")
        return False


def test_rules():
    """Testa as regras de segurança antes do deploy."""
    print("\n🧪 Testando regras de segurança...")

    # Criar arquivo de teste básico se não existir
    test_file = Path("firestore_rules_test.spec.js")
    if not test_file.exists():
        test_content = """
const { assertFails, assertSucceeds, initializeTestEnvironment } = require('@firebase/rules-unit-testing');

describe('Firestore Security Rules', () => {
  let testEnv;

  beforeAll(async () => {
    testEnv = await initializeTestEnvironment({
      projectId: 'knn-benefits-test',
      firestore: {
        rules: require('fs').readFileSync('firestore_rules_production.rules', 'utf8'),
      },
    });
  });

  afterAll(async () => {
    await testEnv.cleanup();
  });

  test('Usuário não autenticado não pode ler dados', async () => {
    const unauthedDb = testEnv.unauthenticatedContext().firestore();
    await assertFails(unauthedDb.collection('students').doc('test').get());
  });

  test('Admin pode ler dados', async () => {
    const adminDb = testEnv.authenticatedContext('admin', {
      role: 'admin',
      tenant_id: 'knn-benefits-tenant'
    }).firestore();

    // Este teste pode falhar se não houver dados, mas a regra deve permitir
    try {
      await adminDb.collection('students').limit(1).get();
    } catch (error) {
      // Ignorar erros de dados não encontrados
      if (!error.message.includes('not found')) {
        throw error;
      }
    }
  });
});
"""
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        print(f"✅ Arquivo de teste criado: {test_file}")

    # Executar testes (se disponível)
    return run_command(
        "firebase emulators:exec --only firestore 'npm test' --project=knn-benefits",
        "Executando testes das regras",
    )


def deploy_rules():
    """Faz deploy das regras de segurança."""
    print("\n🚀 Fazendo deploy das regras de segurança...")

    return run_command(
        "firebase deploy --only firestore:rules --project=knn-benefits",
        "Deploy das regras de segurança",
    )


def deploy_indexes():
    """Faz deploy dos índices."""
    print("\n📊 Fazendo deploy dos índices...")

    return run_command(
        "firebase deploy --only firestore:indexes --project=knn-benefits",
        "Deploy dos índices",
    )


def validate_deployment():
    """Valida se o deploy foi bem-sucedido."""
    print("\n✅ Validando deployment...")

    # Verificar se as regras estão ativas
    return run_command(
        "firebase firestore:rules:get --project=knn-benefits",
        "Verificando regras ativas",
    )


def main():
    """Função principal."""
    print("🔥 Deploy das Regras de Segurança do Firestore - knn-benefits")
    print("=" * 60)

    # Verificar pré-requisitos
    if not check_prerequisites():
        print("\n❌ Pré-requisitos não atendidos. Abortando.")
        sys.exit(1)

    # Verificar autenticação
    if not login_firebase():
        print("\n❌ Problema de autenticação. Abortando.")
        sys.exit(1)

    # Perguntar confirmação
    print("\n⚠️  ATENÇÃO: Você está prestes a fazer deploy das regras de segurança")
    print("   para o ambiente de PRODUÇÃO (knn-benefits).")
    print("   Isso pode afetar o acesso aos dados em produção.")

    confirm = input("\nDeseja continuar? (digite 'CONFIRMO' para prosseguir): ")
    if confirm != "CONFIRMO":
        print("\n❌ Deploy cancelado pelo usuário.")
        sys.exit(0)

    # Testar regras (opcional)
    test_choice = input("\nDeseja executar testes das regras antes do deploy? (s/N): ")
    if test_choice.lower() in ["s", "sim", "y", "yes"]:
        if not test_rules():
            print("\n⚠️ Testes falharam. Deseja continuar mesmo assim?")
            continue_choice = input("Continuar? (s/N): ")
            if continue_choice.lower() not in ["s", "sim", "y", "yes"]:
                print("\n❌ Deploy cancelado devido a falhas nos testes.")
                sys.exit(1)

    # Deploy das regras
    if not deploy_rules():
        print("\n❌ Falha no deploy das regras. Abortando.")
        sys.exit(1)

    # Deploy dos índices
    if not deploy_indexes():
        print("\n⚠️ Falha no deploy dos índices, mas regras foram aplicadas.")
        print("   Você pode tentar fazer deploy dos índices separadamente.")

    # Validar deployment
    validate_deployment()

    print("\n🎉 Deploy concluído com sucesso!")
    print("\n📋 Próximos passos recomendados:")
    print("   1. Verificar logs no Firebase Console")
    print("   2. Testar operações críticas da aplicação")
    print("   3. Monitorar métricas de segurança por 24h")
    print("   4. Documentar mudanças implementadas")

    print("\n🔗 Links úteis:")
    print("   Console: https://console.firebase.google.com/project/knn-benefits")
    print(
        "   Regras: https://console.firebase.google.com/project/knn-benefits/firestore/rules"
    )
    print(
        "   Índices: https://console.firebase.google.com/project/knn-benefits/firestore/indexes"
    )


if __name__ == "__main__":
    main()