#!/usr/bin/env python3
"""
Teste de Autenticação - Employee - Portal KNN

Este script testa especificamente o fluxo de autenticação para usuários Employee,
incluindo endpoints específicos e permissões de funcionários.

Autor: Sistema de Testes KNN
Data: 2025-01-06
"""

import sys
from datetime import datetime

from base_auth_test import BaseAuthenticationTester


class EmployeeAuthenticationTester(BaseAuthenticationTester):
    """Testador específico para autenticação de Employee."""

    def __init__(self):
        """Inicializa o testador de Employee."""
        super().__init__()
        self.entity_type = "employee"

    def test_employee_specific_endpoints(self) -> list[dict]:
        """
        Testa endpoints específicos para Employee.

        Returns:
            Lista com resultados dos testes de endpoints
        """
        self.print_header("TESTANDO ENDPOINTS ESPECÍFICOS DE EMPLOYEE")

        employee_endpoints = [
            "/users/me",
            "/employees/profile",
            "/employees/dashboard",
            "/employees/tasks",
            "/employees/schedule",
            "/employees/reports",
            "/employees/notifications",
            "/employees/students",
            "/employees/courses",
            "/employees/attendance",
            "/employees/performance",
        ]

        endpoint_results = []

        for endpoint in employee_endpoints:
            self.print_step(f"Testando endpoint: {endpoint}")
            success, data = self.test_authenticated_endpoint(endpoint)

            result = {
                "endpoint": endpoint,
                "success": success,
                "timestamp": datetime.now().isoformat(),
            }

            if success and data:
                result["data_keys"] = (
                    list(data.keys()) if isinstance(data, dict) else "non-dict"
                )
                result["data_size"] = len(str(data))

            endpoint_results.append(result)

        successful_endpoints = sum(1 for r in endpoint_results if r["success"])
        total_endpoints = len(endpoint_results)

        self.print_step(
            f"Endpoints testados: {successful_endpoints}/{total_endpoints} bem-sucedidos",
            "SUCCESS" if successful_endpoints > 0 else "WARNING",
        )

        return endpoint_results

    def test_employee_permissions(self) -> dict:
        """
        Testa permissões específicas de Employee.

        Returns:
            Dicionário com resultado do teste de permissões
        """
        self.print_header("TESTANDO PERMISSÕES DE EMPLOYEE")

        permissions_result = {
            "can_access_employee_dashboard": False,
            "can_view_tasks": False,
            "can_view_schedule": False,
            "can_view_reports": False,
            "can_manage_students": False,
            "can_view_courses": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Testar acesso ao dashboard do funcionário
        dashboard_success, _ = self.test_authenticated_endpoint("/employees/dashboard")
        permissions_result["can_access_employee_dashboard"] = dashboard_success

        # Testar acesso a tarefas
        tasks_success, _ = self.test_authenticated_endpoint("/employees/tasks")
        permissions_result["can_view_tasks"] = tasks_success

        # Testar acesso ao cronograma
        schedule_success, _ = self.test_authenticated_endpoint("/employees/schedule")
        permissions_result["can_view_schedule"] = schedule_success

        # Testar acesso a relatórios
        reports_success, _ = self.test_authenticated_endpoint("/employees/reports")
        permissions_result["can_view_reports"] = reports_success

        # Testar gerenciamento de estudantes
        students_success, _ = self.test_authenticated_endpoint("/employees/students")
        permissions_result["can_manage_students"] = students_success

        # Testar acesso a cursos
        courses_success, _ = self.test_authenticated_endpoint("/employees/courses")
        permissions_result["can_view_courses"] = courses_success

        # Resumo das permissões
        total_permissions = 6
        granted_permissions = sum(
            1
            for key, value in permissions_result.items()
            if key.startswith("can_") and value
        )

        self.print_step(
            f"Permissões concedidas: {granted_permissions}/{total_permissions}",
            "SUCCESS" if granted_permissions > 0 else "WARNING",
        )

        return permissions_result

    def test_employee_operational_features(self) -> dict:
        """
        Testa funcionalidades operacionais específicas para Employee.

        Returns:
            Dicionário com resultado dos testes operacionais
        """
        self.print_header("TESTANDO FUNCIONALIDADES OPERACIONAIS - EMPLOYEE")

        operational_result = {
            "can_track_attendance": False,
            "can_view_performance": False,
            "can_access_notifications": False,
            "can_view_profile": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Testar controle de presença
        attendance_success, _ = self.test_authenticated_endpoint(
            "/employees/attendance"
        )
        operational_result["can_track_attendance"] = attendance_success

        # Testar acesso a performance
        performance_success, _ = self.test_authenticated_endpoint(
            "/employees/performance"
        )
        operational_result["can_view_performance"] = performance_success

        # Testar acesso a notificações
        notifications_success, _ = self.test_authenticated_endpoint(
            "/employees/notifications"
        )
        operational_result["can_access_notifications"] = notifications_success

        # Testar acesso ao perfil
        profile_success, _ = self.test_authenticated_endpoint("/employees/profile")
        operational_result["can_view_profile"] = profile_success

        # Resumo das funcionalidades operacionais
        total_tests = 4
        successful_tests = sum(
            1
            for key, value in operational_result.items()
            if key.startswith("can_") and value
        )

        self.print_step(
            f"Funcionalidades operacionais: {successful_tests}/{total_tests} bem-sucedidas",
            "SUCCESS" if successful_tests > 0 else "WARNING",
        )

        return operational_result

    def validate_employee_access_level(self) -> dict:
        """
        Valida o nível de acesso do funcionário (intermediário entre student e admin).

        Returns:
            Dicionário com resultado da validação de nível de acesso
        """
        self.print_header("VALIDANDO NÍVEL DE ACESSO - EMPLOYEE")

        access_level_result = {
            "has_intermediate_access": True,
            "cannot_access_admin_functions": True,
            "can_access_student_management": False,
            "security_validation": "passed",
            "timestamp": datetime.now().isoformat(),
        }

        # Obter informações do usuário
        user_info = self.get_user_info_from_me_endpoint()

        if user_info:
            employee_id = user_info.get("id")
            if employee_id:
                self.print_step(f"🆔 Validando acesso para Employee ID: {employee_id}")
                access_level_result["employee_id"] = employee_id
            else:
                self.print_step("⚠️ ID do funcionário não encontrado", "WARNING")
                access_level_result["security_validation"] = "warning"

        # Testar se NÃO consegue acessar funções administrativas críticas
        admin_users_success, _ = self.test_authenticated_endpoint("/admin/users")
        admin_settings_success, _ = self.test_authenticated_endpoint("/admin/settings")

        if admin_users_success or admin_settings_success:
            self.print_step(
                "❌ FALHA DE SEGURANÇA: Funcionário tem acesso a funções administrativas críticas!",
                "ERROR",
            )
            access_level_result["cannot_access_admin_functions"] = False
            access_level_result["security_validation"] = "failed"

        # Testar se PODE acessar gerenciamento de estudantes (função intermediária)
        students_success, _ = self.test_authenticated_endpoint("/employees/students")
        if students_success:
            self.print_step(
                "✅ Funcionário pode gerenciar estudantes (acesso intermediário correto)",
                "SUCCESS",
            )
            access_level_result["can_access_student_management"] = True

        # Testar se NÃO consegue acessar dados de parceiros
        partner_access_success, _ = self.test_authenticated_endpoint(
            "/partners/dashboard"
        )
        if partner_access_success:
            self.print_step(
                "❌ FALHA DE SEGURANÇA: Funcionário tem acesso a dados de parceiros!",
                "ERROR",
            )
            access_level_result["has_intermediate_access"] = False
            access_level_result["security_validation"] = "failed"

        if access_level_result["security_validation"] == "passed":
            self.print_step(
                "✅ Validação de segurança: Nível de acesso intermediário funcionando corretamente",
                "SUCCESS",
            )

        return access_level_result

    def run_complete_employee_test(self) -> dict:
        """
        Executa o teste completo de autenticação para Employee.

        Returns:
            Dicionário com resultado completo do teste
        """
        self.print_header("TESTE COMPLETO DE AUTENTICAÇÃO - EMPLOYEE")

        # Executar fluxo básico de autenticação
        basic_result = self.run_basic_auth_flow("funcionario_teste")

        if not basic_result["success"]:
            self.print_step(f"Falha no fluxo básico: {basic_result['error']}", "ERROR")
            return basic_result

        # Obter informações detalhadas do usuário
        user_info = self.get_user_info_from_me_endpoint()

        # Testar endpoints específicos de Employee
        endpoint_results = self.test_employee_specific_endpoints()

        # Testar permissões de Employee
        permissions_result = self.test_employee_permissions()

        # Testar funcionalidades operacionais
        operational_result = self.test_employee_operational_features()

        # Validar nível de acesso
        access_level_result = self.validate_employee_access_level()

        # Compilar resultado final
        complete_result = {
            **basic_result,
            "user_info": user_info,
            "endpoint_results": endpoint_results,
            "permissions": permissions_result,
            "operational_features": operational_result,
            "access_level_validation": access_level_result,
            "total_endpoints_tested": len(endpoint_results),
            "successful_endpoints": sum(1 for r in endpoint_results if r["success"]),
            "test_completed_at": datetime.now().isoformat(),
        }

        # Salvar relatório
        report_path = self.save_test_report([complete_result], "employee")

        # Resumo final
        self.print_header("RESUMO DO TESTE - EMPLOYEE")
        self.print_step(
            f"✅ Autenticação Firebase: {'Sucesso' if basic_result['success'] else 'Falha'}"
        )
        self.print_step(
            f"✅ Login Backend: {'Sucesso' if basic_result['success'] else 'Falha'}"
        )
        self.print_step(
            f"📊 Endpoints testados: {complete_result['successful_endpoints']}/{complete_result['total_endpoints_tested']}"
        )
        self.print_step(
            f"🔒 Validação de segurança: {access_level_result['security_validation'].upper()}"
        )

        if user_info:
            self.print_step(f"👤 Usuário: {user_info.get('email', 'N/A')}")
            self.print_step(f"🆔 ID: {user_info.get('id', 'N/A')}")
            self.print_step(f"👥 Role: {user_info.get('role', 'N/A')}")
            self.print_step(f"💼 Employee ID: {user_info.get('employee_id', 'N/A')}")

        self.print_step(f"📄 Relatório salvo: {report_path}")

        return complete_result


def main():
    """Função principal para execução do teste de Employee."""
    print("🔐 Iniciando Teste de Autenticação - EMPLOYEE")
    print(f"⏰ Horário: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        tester = EmployeeAuthenticationTester()
        result = tester.run_complete_employee_test()

        if result["success"]:
            print("\n🎉 Teste de Employee concluído com SUCESSO!")
            sys.exit(0)
        else:
            print(
                f"\n❌ Teste de Employee FALHOU: {result.get('error', 'Erro desconhecido')}"
            )
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erro inesperado no teste: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
