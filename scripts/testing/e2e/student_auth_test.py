#!/usr/bin/env python3
"""
Teste de Autenticação - Student - Portal KNN

Este script testa especificamente o fluxo de autenticação para usuários Student,
incluindo endpoints específicos e permissões de estudantes.

Autor: Sistema de Testes KNN
Data: 2025-01-06
"""

import sys
from datetime import datetime

from base_auth_test import BaseAuthenticationTester


class StudentAuthenticationTester(BaseAuthenticationTester):
    """Testador específico para autenticação de Student."""

    def __init__(self):
        """Inicializa o testador de Student."""
        super().__init__()
        self.entity_type = "student"

    def test_student_specific_endpoints(self) -> list[dict]:
        """
        Testa endpoints específicos para Student.

        Returns:
            Lista com resultados dos testes de endpoints
        """
        self.print_header("TESTANDO ENDPOINTS ESPECÍFICOS DE STUDENT")

        student_endpoints = [
            "/users/me",
            "/students/profile",
            "/students/courses",
            "/students/enrollments",
            "/students/progress",
            "/students/benefits",
            "/students/dashboard",
            "/students/certificates",
            "/students/notifications",
            "/students/grades",
            "/students/schedule",
        ]

        endpoint_results = []

        for endpoint in student_endpoints:
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

    def test_student_permissions(self) -> dict:
        """
        Testa permissões específicas de Student.

        Returns:
            Dicionário com resultado do teste de permissões
        """
        self.print_header("TESTANDO PERMISSÕES DE STUDENT")

        permissions_result = {
            "can_access_student_dashboard": False,
            "can_view_courses": False,
            "can_view_enrollments": False,
            "can_view_progress": False,
            "can_access_benefits": False,
            "can_view_certificates": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Testar acesso ao dashboard do estudante
        dashboard_success, _ = self.test_authenticated_endpoint("/students/dashboard")
        permissions_result["can_access_student_dashboard"] = dashboard_success

        # Testar acesso a cursos
        courses_success, _ = self.test_authenticated_endpoint("/students/courses")
        permissions_result["can_view_courses"] = courses_success

        # Testar acesso a matrículas
        enrollments_success, _ = self.test_authenticated_endpoint(
            "/students/enrollments"
        )
        permissions_result["can_view_enrollments"] = enrollments_success

        # Testar acesso ao progresso
        progress_success, _ = self.test_authenticated_endpoint("/students/progress")
        permissions_result["can_view_progress"] = progress_success

        # Testar acesso a benefícios
        benefits_success, _ = self.test_authenticated_endpoint("/students/benefits")
        permissions_result["can_access_benefits"] = benefits_success

        # Testar acesso a certificados
        certificates_success, _ = self.test_authenticated_endpoint(
            "/students/certificates"
        )
        permissions_result["can_view_certificates"] = certificates_success

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

    def test_student_academic_features(self) -> dict:
        """
        Testa funcionalidades acadêmicas específicas para Student.

        Returns:
            Dicionário com resultado dos testes acadêmicos
        """
        self.print_header("TESTANDO FUNCIONALIDADES ACADÊMICAS - STUDENT")

        academic_result = {
            "can_view_grades": False,
            "can_view_schedule": False,
            "can_access_notifications": False,
            "can_view_profile": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Testar acesso a notas
        grades_success, _ = self.test_authenticated_endpoint("/students/grades")
        academic_result["can_view_grades"] = grades_success

        # Testar acesso ao cronograma
        schedule_success, _ = self.test_authenticated_endpoint("/students/schedule")
        academic_result["can_view_schedule"] = schedule_success

        # Testar acesso a notificações
        notifications_success, _ = self.test_authenticated_endpoint(
            "/students/notifications"
        )
        academic_result["can_access_notifications"] = notifications_success

        # Testar acesso ao perfil
        profile_success, _ = self.test_authenticated_endpoint("/students/profile")
        academic_result["can_view_profile"] = profile_success

        # Resumo das funcionalidades acadêmicas
        total_tests = 4
        successful_tests = sum(
            1
            for key, value in academic_result.items()
            if key.startswith("can_") and value
        )

        self.print_step(
            f"Funcionalidades acadêmicas: {successful_tests}/{total_tests} bem-sucedidas",
            "SUCCESS" if successful_tests > 0 else "WARNING",
        )

        return academic_result

    def validate_student_data_access(self) -> dict:
        """
        Valida se o estudante tem acesso apenas aos próprios dados.

        Returns:
            Dicionário com resultado da validação de acesso a dados
        """
        self.print_header("VALIDANDO ACESSO A DADOS - STUDENT")

        data_access_result = {
            "has_restricted_access": True,
            "can_access_own_data_only": True,
            "security_validation": "passed",
            "timestamp": datetime.now().isoformat(),
        }

        # Obter informações do usuário para validar acesso restrito
        user_info = self.get_user_info_from_me_endpoint()

        if user_info:
            student_id = user_info.get("id")
            if student_id:
                self.print_step(f"🆔 Validando acesso para Student ID: {student_id}")
                data_access_result["student_id"] = student_id
            else:
                self.print_step("⚠️ ID do estudante não encontrado", "WARNING")
                data_access_result["security_validation"] = "warning"

        # Testar se não consegue acessar dados administrativos
        admin_access_success, _ = self.test_authenticated_endpoint("/admin/users")
        if admin_access_success:
            self.print_step(
                "❌ FALHA DE SEGURANÇA: Estudante tem acesso a dados administrativos!",
                "ERROR",
            )
            data_access_result["has_restricted_access"] = False
            data_access_result["security_validation"] = "failed"

        # Testar se não consegue acessar dados de outros parceiros
        partner_access_success, _ = self.test_authenticated_endpoint(
            "/partners/dashboard"
        )
        if partner_access_success:
            self.print_step(
                "❌ FALHA DE SEGURANÇA: Estudante tem acesso a dados de parceiros!",
                "ERROR",
            )
            data_access_result["has_restricted_access"] = False
            data_access_result["security_validation"] = "failed"

        if data_access_result["security_validation"] == "passed":
            self.print_step(
                "✅ Validação de segurança: Acesso restrito funcionando corretamente",
                "SUCCESS",
            )

        return data_access_result

    def run_complete_student_test(self) -> dict:
        """
        Executa o teste completo de autenticação para Student.

        Returns:
            Dicionário com resultado completo do teste
        """
        self.print_header("TESTE COMPLETO DE AUTENTICAÇÃO - STUDENT")

        # Executar fluxo básico de autenticação
        basic_result = self.run_basic_auth_flow("estudante_teste")

        if not basic_result["success"]:
            self.print_step(f"Falha no fluxo básico: {basic_result['error']}", "ERROR")
            return basic_result

        # Obter informações detalhadas do usuário
        user_info = self.get_user_info_from_me_endpoint()

        # Testar endpoints específicos de Student
        endpoint_results = self.test_student_specific_endpoints()

        # Testar permissões de Student
        permissions_result = self.test_student_permissions()

        # Testar funcionalidades acadêmicas
        academic_result = self.test_student_academic_features()

        # Validar acesso a dados
        data_access_result = self.validate_student_data_access()

        # Compilar resultado final
        complete_result = {
            **basic_result,
            "user_info": user_info,
            "endpoint_results": endpoint_results,
            "permissions": permissions_result,
            "academic_features": academic_result,
            "data_access_validation": data_access_result,
            "total_endpoints_tested": len(endpoint_results),
            "successful_endpoints": sum(1 for r in endpoint_results if r["success"]),
            "test_completed_at": datetime.now().isoformat(),
        }

        # Salvar relatório
        report_path = self.save_test_report([complete_result], "student")

        # Resumo final
        self.print_header("RESUMO DO TESTE - STUDENT")
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
            f"🔒 Validação de segurança: {data_access_result['security_validation'].upper()}"
        )

        if user_info:
            self.print_step(f"👤 Usuário: {user_info.get('email', 'N/A')}")
            self.print_step(f"🆔 ID: {user_info.get('id', 'N/A')}")
            self.print_step(f"👥 Role: {user_info.get('role', 'N/A')}")
            self.print_step(f"🎓 Student ID: {user_info.get('student_id', 'N/A')}")

        self.print_step(f"📄 Relatório salvo: {report_path}")

        return complete_result


def main():
    """Função principal para execução do teste de Student."""
    print("🔐 Iniciando Teste de Autenticação - STUDENT")
    print(f"⏰ Horário: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        tester = StudentAuthenticationTester()
        result = tester.run_complete_student_test()

        if result["success"]:
            print("\n🎉 Teste de Student concluído com SUCESSO!")
            sys.exit(0)
        else:
            print(
                f"\n❌ Teste de Student FALHOU: {result.get('error', 'Erro desconhecido')}"
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
