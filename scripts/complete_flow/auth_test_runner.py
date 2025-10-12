#!/usr/bin/env python3
"""
Runner de Testes de Autenticação - Portal KNN

Este script permite executar testes de autenticação de forma interativa,
escolhendo qual entidade testar ou executando todos os testes.

Autor: Sistema de Testes KNN
Data: 2025-01-06
"""

import os
import sys
import argparse
from datetime import datetime

# Importar os testadores específicos
try:
    from admin_auth_test import AdminAuthenticationTester
    from employee_auth_test import EmployeeAuthenticationTester
    from partner_auth_test import PartnerAuthenticationTester
    from student_auth_test import StudentAuthenticationTester
except ImportError as e:
    print(f"❌ Erro ao importar módulos de teste: {e}")
    print("Certifique-se de que todos os arquivos de teste estão no mesmo diretório.")
    sys.exit(1)


class AuthTestRunner:
    """Classe principal para executar testes de autenticação."""

    def __init__(self):
        """Inicializa o runner de testes."""
        self.available_tests = {
            "1": {
                "name": "Admin",
                "description": "Teste de autenticação para Administradores",
                "tester_class": AdminAuthenticationTester,
                "icon": "👑",
            },
            "2": {
                "name": "Partner",
                "description": "Teste de autenticação para Parceiros",
                "tester_class": PartnerAuthenticationTester,
                "icon": "🤝",
            },
            "3": {
                "name": "Student",
                "description": "Teste de autenticação para Estudantes",
                "tester_class": StudentAuthenticationTester,
                "icon": "🎓",
            },
            "4": {
                "name": "Employee",
                "description": "Teste de autenticação para Funcionários",
                "tester_class": EmployeeAuthenticationTester,
                "icon": "💼",
            },
        }

    def print_header(self) -> None:
        """Imprime o cabeçalho do programa."""
        print("\n" + "=" * 70)
        print("🔐 RUNNER DE TESTES DE AUTENTICAÇÃO - PORTAL KNN")
        print("=" * 70)
        print(f"⏰ Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"📁 Diretório: {os.getcwd()}")
        print("=" * 70)

    def print_menu(self) -> None:
        """Imprime o menu de opções."""
        print("\n📋 OPÇÕES DISPONÍVEIS:")
        print("-" * 50)

        for key, test_info in self.available_tests.items():
            print(f"{key}. {test_info['icon']} {test_info['name']} - {test_info['description']}")

        print("5. 🚀 Executar TODOS os testes")
        print("6. 📊 Executar testes com relatório consolidado")
        print("0. ❌ Sair")
        print("-" * 50)

    def get_user_choice(self) -> str:
        """
        Obtém a escolha do usuário.

        Returns:
            String com a opção escolhida
        """
        while True:
            try:
                choice = input("\n👉 Digite sua opção: ").strip()
                if choice in ["0", "1", "2", "3", "4", "5", "6"]:
                    return choice
                else:
                    print("❌ Opção inválida! Digite um número de 0 a 6.")
            except KeyboardInterrupt:
                print("\n\n⚠️ Operação cancelada pelo usuário.")
                sys.exit(0)
            except EOFError:
                print("\n\n⚠️ Entrada finalizada.")
                sys.exit(0)

    def run_single_test(self, test_key: str) -> dict:
        """
        Executa um teste específico.

        Args:
            test_key: Chave do teste a ser executado

        Returns:
            Dicionário com resultado do teste
        """
        if test_key not in self.available_tests:
            return {"success": False, "error": f"Teste '{test_key}' não encontrado"}

        test_info = self.available_tests[test_key]

        print(f"\n🚀 Iniciando teste: {test_info['icon']} {test_info['name']}")
        print(f"📝 Descrição: {test_info['description']}")
        print("-" * 60)

        try:
            # Instanciar o testador específico
            tester = test_info["tester_class"]()

            # Executar o teste completo
            if hasattr(tester, f"run_complete_{test_info['name'].lower()}_test"):
                result = getattr(tester, f"run_complete_{test_info['name'].lower()}_test")()
            else:
                result = {"success": False, "error": "Método de teste não encontrado"}

            return result

        except Exception as e:
            return {"success": False, "error": f"Erro inesperado: {str(e)}"}

    def run_all_tests(self) -> dict:
        """
        Executa todos os testes disponíveis.

        Returns:
            Dicionário com resultados consolidados
        """
        print("\n🚀 EXECUTANDO TODOS OS TESTES")
        print("=" * 60)

        all_results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.available_tests),
            "successful_tests": 0,
            "failed_tests": 0,
            "test_results": {},
        }

        for test_key, test_info in self.available_tests.items():
            print(f"\n📋 Executando: {test_info['icon']} {test_info['name']}")

            result = self.run_single_test(test_key)
            all_results["test_results"][test_info["name"].lower()] = result

            if result.get("success", False):
                all_results["successful_tests"] += 1
                print(f"✅ {test_info['name']}: SUCESSO")
            else:
                all_results["failed_tests"] += 1
                print(f"❌ {test_info['name']}: FALHA - {result.get('error', 'Erro desconhecido')}")

        return all_results

    def save_consolidated_report(self, all_results: dict) -> str:
        """
        Salva um relatório consolidado de todos os testes.

        Args:
            all_results: Dicionário com resultados de todos os testes

        Returns:
            Caminho do arquivo salvo
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"consolidated_auth_test_report_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)

        try:
            import json
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)

            print(f"\n📄 Relatório consolidado salvo: {filepath}")
            return filepath

        except Exception as e:
            print(f"\n❌ Erro ao salvar relatório consolidado: {str(e)}")
            return ""

    def print_summary(self, all_results: dict) -> None:
        """
        Imprime um resumo dos resultados.

        Args:
            all_results: Dicionário com resultados de todos os testes
        """
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)

        print(f"📈 Total de testes: {all_results['total_tests']}")
        print(f"✅ Testes bem-sucedidos: {all_results['successful_tests']}")
        print(f"❌ Testes falharam: {all_results['failed_tests']}")

        success_rate = (all_results['successful_tests'] / all_results['total_tests']) * 100
        print(f"📊 Taxa de sucesso: {success_rate:.1f}%")

        print("\n📋 DETALHES POR TESTE:")
        print("-" * 40)

        for entity, result in all_results["test_results"].items():
            status = "✅ SUCESSO" if result.get("success", False) else "❌ FALHA"
            endpoints = result.get("successful_endpoints", 0)
            total_endpoints = result.get("total_endpoints_tested", 0)

            print(f"{entity.upper():12} | {status:10} | Endpoints: {endpoints}/{total_endpoints}")

        print("=" * 60)

    def run_interactive_mode(self) -> None:
        """Executa o modo interativo do runner."""
        self.print_header()

        while True:
            self.print_menu()
            choice = self.get_user_choice()

            if choice == "0":
                print("\n👋 Encerrando programa. Até logo!")
                break

            elif choice in ["1", "2", "3", "4"]:
                # Executar teste específico
                result = self.run_single_test(choice)

                if result.get("success", False):
                    print("\n🎉 Teste concluído com SUCESSO!")
                else:
                    print(f"\n❌ Teste FALHOU: {result.get('error', 'Erro desconhecido')}")

                input("\n⏸️ Pressione ENTER para continuar...")

            elif choice == "5":
                # Executar todos os testes
                all_results = self.run_all_tests()
                self.print_summary(all_results)

                input("\n⏸️ Pressione ENTER para continuar...")

            elif choice == "6":
                # Executar todos os testes com relatório consolidado
                all_results = self.run_all_tests()
                self.save_consolidated_report(all_results)
                self.print_summary(all_results)

                input("\n⏸️ Pressione ENTER para continuar...")

    def run_command_line_mode(self, entity: str) -> None:
        """
        Executa um teste específico via linha de comando.

        Args:
            entity: Nome da entidade a ser testada (admin, partner, student, employee)
        """
        entity_map = {
            "admin": "1",
            "partner": "2",
            "student": "3",
            "employee": "4",
        }

        test_key = entity_map.get(entity.lower())

        if not test_key:
            print(f"❌ Entidade '{entity}' não reconhecida.")
            print("Entidades disponíveis: admin, partner, student, employee")
            sys.exit(1)

        self.print_header()
        result = self.run_single_test(test_key)

        if result.get("success", False):
            print(f"\n🎉 Teste de {entity.upper()} concluído com SUCESSO!")
            sys.exit(0)
        else:
            print(f"\n❌ Teste de {entity.upper()} FALHOU: {result.get('error', 'Erro desconhecido')}")
            sys.exit(1)


def main():
    """Função principal do programa."""
    runner = AuthTestRunner()

    parser = argparse.ArgumentParser(description="Runner de Testes de Autenticação - Portal KNN")
    parser.add_argument(
        "--test",
        type=str,
        choices=["admin", "partner", "student", "employee", "all"],
        help="Executa um teste específico (admin, partner, student, employee) ou todos ('all'). Se omitido, entra em modo interativo."
    )
    args = parser.parse_args()

    if args.test:
        if args.test == "all":
            runner.print_header()
            all_results = runner.run_all_tests()
            runner.print_summary(all_results)
            sys.exit(1 if all_results.get("failed_tests", 0) > 0 else 0)
        else:
            runner.run_command_line_mode(args.test)
    else:
        # Modo interativo
        try:
            runner.run_interactive_mode()
        except KeyboardInterrupt:
            print("\n\n⚠️ Programa interrompido pelo usuário.")
            sys.exit(0)
        except Exception as e:
            print(f"\n💥 Erro inesperado: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
