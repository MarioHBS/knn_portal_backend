#!/usr/bin/env python3
"""
Script de Configuração do Ambiente de Teste de Autenticação

Este script ajuda a configurar o ambiente necessário para executar
os testes de autenticação completos do Portal KNN.

Autor: Sistema de Testes KNN
Data: 2025-01-06
"""

import os
import sys
from pathlib import Path


def print_header(title: str) -> None:
    """Imprime um cabeçalho formatado."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step: str, status: str = "INFO") -> None:
    """Imprime uma etapa do processo."""
    status_icon = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️"
    }.get(status, "ℹ️")

    print(f"{status_icon} {step}")

def check_environment() -> dict:
    """
    Verifica o estado atual do ambiente.

    Returns:
        Dicionário com status das verificações
    """
    checks = {
        "firebase_api_key": bool(os.getenv("FIREBASE_API_KEY")),
        "project_root": Path.cwd().name == "knn_portal_journey_club_backend",
        "venv_active": hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix),
        "backend_running": False  # Será verificado separadamente
    }

    return checks

def setup_firebase_api_key() -> None:
    """Ajuda o usuário a configurar a FIREBASE_API_KEY."""
    print_header("CONFIGURAÇÃO DA FIREBASE API KEY")

    current_key = os.getenv("FIREBASE_API_KEY")

    if current_key:
        print_step(f"FIREBASE_API_KEY já configurada: {current_key[:10]}...", "SUCCESS")
        return

    print_step("FIREBASE_API_KEY não encontrada", "WARNING")
    print("\nPara obter sua Firebase API Key:")
    print("1. Acesse o Console do Firebase: https://console.firebase.google.com/")
    print("2. Selecione o projeto 'knn-benefits'")
    print("3. Vá em 'Configurações do projeto' (ícone de engrenagem)")
    print("4. Na aba 'Geral', role até 'Seus aplicativos'")
    print("5. Copie a 'Chave da API da Web'")

    print("\nFormas de configurar a API Key:")
    print("1. Variável de ambiente temporária:")
    print("   set FIREBASE_API_KEY=sua_api_key_aqui")
    print("\n2. Arquivo .env (recomendado):")
    print("   Adicione a linha: FIREBASE_API_KEY=sua_api_key_aqui")

    api_key = input("\nCole sua Firebase API Key aqui (ou Enter para pular): ").strip()

    if api_key:
        # Configurar temporariamente para esta sessão
        os.environ["FIREBASE_API_KEY"] = api_key
        print_step("API Key configurada temporariamente para esta sessão", "SUCCESS")

        # Sugerir adicionar ao .env
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            print_step("Recomendação: Adicione a API Key ao arquivo .env para uso permanente", "INFO")
        else:
            print_step("Recomendação: Crie um arquivo .env com a API Key", "INFO")

def create_quick_test_script() -> None:
    """Cria um script de teste rápido."""
    print_header("CRIAÇÃO DE SCRIPT DE TESTE RÁPIDO")

    script_content = '''#!/usr/bin/env python3
"""
Teste Rápido de Autenticação - Gerado automaticamente
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.testing.complete_auth_flow_test import AuthenticationTester

def quick_test():
    """Executa um teste rápido com o usuário padrão."""
    print("🚀 Teste Rápido de Autenticação")
    print("=" * 40)

    tester = AuthenticationTester()

    # Usar parceiro_teste como padrão
    result = tester.run_complete_test("parceiro_teste")

    if result["success"]:
        print("\\n✅ Teste rápido bem-sucedido!")
    else:
        print("\\n❌ Teste rápido falhou")

    return result["success"]

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
'''

    script_path = Path.cwd() / "scripts" / "testing" / "quick_auth_test.py"

    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        print_step(f"Script de teste rápido criado: {script_path}", "SUCCESS")
        print_step("Execute com: python scripts/testing/quick_auth_test.py", "INFO")
    except Exception as e:
        print_step(f"Erro ao criar script: {e}", "ERROR")

def check_backend_status() -> bool:
    """Verifica se o backend está rodando."""
    try:
        import requests
        response = requests.get("http://localhost:8080/v1/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def main():
    """Função principal do script de configuração."""
    print("🔧 Configuração do Ambiente de Teste de Autenticação")
    print("=" * 60)

    # Verificar estado atual
    print_header("VERIFICAÇÃO DO AMBIENTE")

    checks = check_environment()

    print_step(f"Diretório correto: {'Sim' if checks['project_root'] else 'Não'}",
               "SUCCESS" if checks['project_root'] else "ERROR")

    print_step(f"Ambiente virtual ativo: {'Sim' if checks['venv_active'] else 'Não'}",
               "SUCCESS" if checks['venv_active'] else "WARNING")

    print_step(f"Firebase API Key: {'Configurada' if checks['firebase_api_key'] else 'Não configurada'}",
               "SUCCESS" if checks['firebase_api_key'] else "WARNING")

    # Verificar backend
    backend_running = check_backend_status()
    print_step(f"Backend rodando: {'Sim' if backend_running else 'Não'}",
               "SUCCESS" if backend_running else "WARNING")

    # Configurações necessárias
    if not checks['project_root']:
        print_step("Execute este script do diretório raiz do projeto", "ERROR")
        return 1

    if not checks['venv_active']:
        print_step("Recomendado: Ative o ambiente virtual (.venv)", "WARNING")
        print("Execute: .venv\\Scripts\\activate")

    if not checks['firebase_api_key']:
        setup_firebase_api_key()

    if not backend_running:
        print_step("Backend não está rodando", "WARNING")
        print("Para iniciar o backend:")
        print("1. Ative o ambiente virtual: .venv\\Scripts\\activate")
        print("2. Execute: python scripts/run_server.py")

    # Criar script de teste rápido
    create_quick_test_script()

    # Resumo final
    print_header("RESUMO DA CONFIGURAÇÃO")

    all_ready = all([
        checks['project_root'],
        checks['firebase_api_key'] or os.getenv("FIREBASE_API_KEY"),
        backend_running
    ])

    if all_ready:
        print_step("✅ Ambiente configurado e pronto para testes!", "SUCCESS")
        print("\nPróximos passos:")
        print("1. Execute: python scripts/testing/complete_auth_flow_test.py")
        print("2. Ou teste rápido: python scripts/testing/quick_auth_test.py")
    else:
        print_step("⚠️ Algumas configurações ainda precisam ser ajustadas", "WARNING")
        print("\nVerifique os itens marcados acima e execute novamente.")

    return 0 if all_ready else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
