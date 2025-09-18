#!/usr/bin/env python3
"""
Script para verificar se os dados de funcionários foram transferidos corretamente para o Firestore.
"""

import os
import sys

# Adicionar o diretório raiz do projeto ao path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import firebase_admin
from firebase_admin import firestore, initialize_app


class EmployeesVerifier:
    def __init__(self):
        self.db = None

    def initialize_firestore(self):
        """Inicializa a conexão com o Firestore"""
        try:
            # Tentar usar credenciais padrão primeiro
            if not firebase_admin._apps:
                initialize_app()

            self.db = firestore.client()
            print("✅ Conectado ao Firestore com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro ao conectar com Firestore: {e}")
            return False

    def verify_employees_data(self):
        """Verifica os dados de funcionários no Firestore"""
        try:
            print("\n🔍 Verificando dados de funcionários no Firestore...")

            employees_ref = self.db.collection("employees")
            employees = list(employees_ref.stream())

            print(f"📊 Total de funcionários encontrados: {len(employees)}")

            if len(employees) > 0:
                print("\n👥 Lista de funcionários:")
                print("-" * 80)

                for i, employee in enumerate(employees, 1):
                    data = employee.to_dict()
                    print(f"{i:2d}. ID: {employee.id}")
                    print(f"    Nome: {data.get('name', 'N/A')}")
                    print(f"    Cargo: {data.get('role', 'N/A')}")
                    print(f"    Email: {data.get('e-mail', 'N/A')}")
                    print(f"    Tenant: {data.get('tenant_id', 'N/A')}")
                    print(f"    Ativo: {data.get('active', 'N/A')}")

                    # Verificar se o campo 'id' foi excluído dos dados
                    if "id" in data:
                        print(
                            f"    ⚠️  ATENÇÃO: Campo 'id' encontrado nos dados: {data['id']}"
                        )
                    else:
                        print("    ✅ Campo 'id' corretamente excluído dos dados")

                    print()

                print("-" * 80)
                print(
                    f"✅ Verificação concluída: {len(employees)} funcionários encontrados"
                )

                # Verificar se algum funcionário tem campo 'id' nos dados
                employees_with_id = [emp for emp in employees if "id" in emp.to_dict()]
                if employees_with_id:
                    print(
                        f"⚠️  ATENÇÃO: {len(employees_with_id)} funcionários têm campo 'id' nos dados"
                    )
                else:
                    print("✅ Nenhum funcionário tem campo 'id' nos dados (correto!)")

            else:
                print("❌ Nenhum funcionário encontrado no Firestore")
                return False

            return True

        except Exception as e:
            print(f"❌ Erro ao verificar funcionários: {e}")
            return False

    def run(self):
        """Executa a verificação completa"""
        print("=" * 60)
        print("🔍 VERIFICAÇÃO DE FUNCIONÁRIOS NO FIRESTORE")
        print("=" * 60)

        # Inicializar Firestore
        if not self.initialize_firestore():
            return False

        # Verificar dados
        success = self.verify_employees_data()

        if success:
            print("\n" + "=" * 60)
            print("✅ VERIFICAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ VERIFICAÇÃO FALHOU!")
            print("=" * 60)

        return success


def main():
    verifier = EmployeesVerifier()
    return verifier.run()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)