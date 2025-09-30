#!/usr/bin/env python3
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
        print("\n✅ Teste rápido bem-sucedido!")
    else:
        print("\n❌ Teste rápido falhou")
        
    return result["success"]

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
