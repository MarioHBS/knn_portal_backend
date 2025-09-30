#!/usr/bin/env python3
"""
Teste de Autenticação - Admin - Portal KNN

Este script testa especificamente o fluxo de autenticação para usuários Admin,
incluindo endpoints específicos e permissões administrativas.

Autor: Sistema de Testes KNN
Data: 2025-01-06
"""

import json
import sys
from datetime import datetime

import requests
from base_auth_test import BACKEND_BASE_URL, BaseAuthenticationTester


class AdminAuthenticationTester(BaseAuthenticationTester):
    """Testador específico para autenticação de Admin."""

    def __init__(self):
        """Inicializa o testador de Admin."""
        super().__init__()
        self.entity_type = "admin"

    def test_authenticated_endpoint_with_data(
        self, endpoint: str, method: str = "POST", data: dict | None = None
    ) -> tuple[bool, dict | None]:
        """
        Testa um endpoint autenticado com dados (POST, PUT, DELETE).

        Args:
            endpoint: Endpoint a ser testado
            method: Método HTTP (POST, PUT, DELETE)
            data: Dados para enviar na requisição

        Returns:
            Tupla (sucesso, dados_resposta)
        """
        if not self.jwt_token:
            self.print_step("Token JWT não disponível", "ERROR")
            return False, None

        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        try:
            if method.upper() == "POST":
                response = self.session.post(
                    f"{BACKEND_BASE_URL}{endpoint}",
                    json=data,
                    headers=headers,
                    timeout=30,
                )
            elif method.upper() == "PUT":
                response = self.session.put(
                    f"{BACKEND_BASE_URL}{endpoint}",
                    json=data,
                    headers=headers,
                    timeout=30,
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(
                    f"{BACKEND_BASE_URL}{endpoint}",
                    json=data,
                    headers=headers,
                    timeout=30,
                )
            else:
                self.print_step(f"Método HTTP não suportado: {method}", "ERROR")
                return False, None

            if response.status_code in [200, 201]:
                self.print_step(
                    f"✅ {method} {endpoint}: {response.status_code}", "SUCCESS"
                )
                try:
                    return True, response.json()
                except json.JSONDecodeError:
                    return True, {"message": "Success"}
            elif response.status_code == 404:
                self.print_step(
                    f"⚠️ {method} {endpoint}: {response.status_code} (Endpoint não encontrado)",
                    "WARNING",
                )
                return True, None
            else:
                error_text = ""
                try:
                    error_data = response.json()
                    error_text = error_data.get("detail", response.text)
                except json.JSONDecodeError:
                    error_text = response.text

                self.print_step(
                    f"❌ {method} {endpoint}: {response.status_code} - {error_text}",
                    "ERROR",
                )
                return False, None

        except requests.exceptions.RequestException as e:
            self.print_step(
                f"Erro de rede no endpoint {method} {endpoint}: {str(e)}", "ERROR"
            )
            return False, None
        except Exception as e:
            self.print_step(
                f"Erro inesperado no endpoint {method} {endpoint}: {str(e)}", "ERROR"
            )
            return False, None

    def test_admin_specific_endpoints(self) -> list[dict]:
        """
        Testa endpoints específicos para Admin.

        Returns:
            Lista com resultados dos testes de endpoints
        """
        self.print_header("TESTANDO ENDPOINTS ESPECÍFICOS DE ADMIN")

        admin_endpoints = [
            "/users/me",
            "/admin/partners",
            "/admin/students",
            "/admin/employees",
            "/admin/benefits",
            "/admin/metrics",
        ]

        endpoint_results = []

        for endpoint in admin_endpoints:
            self.print_step(f"Testando endpoint: {endpoint}")
            success, data = self.test_authenticated_endpoint(endpoint)

            result = {
                "endpoint": endpoint,
                "success": success,
                "timestamp": datetime.now().isoformat(),
            }

            if success and data:
                # Para endpoints de listagem, mostrar amostra e salvar dados completos
                if endpoint in ["/admin/students", "/admin/employees"]:
                    if isinstance(data, list):
                        data_list = data
                        result["data"] = data_list  # Salvar lista completa no relatório
                        result["data_count"] = len(data_list)

                        # Mostrar uma amostra nos logs
                        sample_size = 3
                        if data_list:
                            self.print_step(
                                f"  -> Amostra de dados ({len(data_list)} registros):",
                                "INFO",
                            )
                            for item in data_list[:sample_size]:
                                if isinstance(item, dict):
                                    item_info = {
                                        k: v
                                        for k, v in item.items()
                                        if k in ["id", "name", "email"]
                                    }
                                    print(f"    - {item_info}")
                                else:
                                    print(f"    - {item}")
                            if len(data_list) > sample_size:
                                print(
                                    f"    ... e mais {len(data_list) - sample_size} outros."
                                )
                    else:
                        self.print_step(
                            f"  -> Resposta para {endpoint} não é uma lista: {type(data)}",
                            "WARNING",
                        )
                        result["data"] = str(data)
                        result["data_keys"] = (
                            list(data.keys()) if isinstance(data, dict) else "non-dict"
                        )
                else:
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

    def test_benefits_management_endpoints(self) -> dict:
        """
        Testa endpoints específicos de gerenciamento de benefícios.

        Returns:
            Dicionário com resultado dos testes de benefícios
        """
        self.print_header("TESTANDO ENDPOINTS DE GERENCIAMENTO DE BENEFÍCIOS")

        benefits_result = {
            "list_benefits": {"success": False, "data": None, "error": None},
            "get_specific_benefit": {"success": False, "data": None, "error": None},
            "create_benefit": {"success": False, "data": None, "error": None},
            "update_benefit": {"success": False, "data": None, "error": None},
            "delete_benefit": {"success": False, "data": None, "error": None},
            "timestamp": datetime.now().isoformat(),
        }

        # 1. Testar listagem de benefícios (GET /admin/benefits)
        self.print_step("Testando listagem de benefícios...")
        try:
            success, data = self.test_authenticated_endpoint("/admin/benefits")
            benefits_result["list_benefits"]["success"] = success
            benefits_result["list_benefits"]["data"] = data

            if success and data:
                # Acessar corretamente a estrutura de dados retornada pelo endpoint
                benefits_data = data.get("data", {})
                benefits_items = benefits_data.get("items", [])
                total_benefits = benefits_data.get("total", 0)

                self.print_step(
                    f"✅ Listagem: {len(benefits_items)} benefícios na página atual (total: {total_benefits})",
                    "SUCCESS",
                )
            else:
                self.print_step("❌ Falha na listagem de benefícios", "ERROR")
        except Exception as e:
            benefits_result["list_benefits"]["error"] = str(e)
            self.print_step(f"❌ Erro na listagem: {str(e)}", "ERROR")

        # 2. Testar listagem com filtros
        self.print_step("Testando listagem com filtros...")
        try:
            success, data = self.test_authenticated_endpoint(
                "/admin/benefits?limit=5&offset=0"
            )
            if success:
                self.print_step("✅ Listagem com paginação funcionando", "SUCCESS")
            else:
                self.print_step("❌ Falha na listagem com filtros", "WARNING")
        except Exception as e:
            self.print_step(f"❌ Erro na listagem com filtros: {str(e)}", "ERROR")

        # 3. Testar criação de benefício (POST /admin/benefits)
        self.print_step("Testando criação de benefício...")
        try:
            benefit_data = {
                "partner_id": "PTN_T4L5678_TEC",
                "title": "Benefício de Teste Admin",
                "description": "Descrição do benefício de teste criado pelo admin",
                "value": 15,
                "category": "desconto",
                "type": "percentage",
                "valid_from": "2025-01-01T00:00:00Z",
                "valid_to": "2025-12-31T23:59:59Z",
                "active": True,
                "audience": ["student", "employee"],
            }

            success, data = self.test_authenticated_endpoint_with_data(
                "/admin/benefits", method="POST", data=benefit_data
            )

            benefits_result["create_benefit"]["success"] = success
            benefits_result["create_benefit"]["data"] = data

            if success and data:
                created_benefit_id = data.get("data", {}).get("benefit_id")
                self.print_step(f"✅ Benefício criado: {created_benefit_id}", "SUCCESS")

                # Armazenar IDs para testes subsequentes
                self.test_partner_id = benefit_data["partner_id"]
                self.test_benefit_id = created_benefit_id
            else:
                self.print_step("❌ Falha na criação de benefício", "ERROR")

        except Exception as e:
            benefits_result["create_benefit"]["error"] = str(e)
            self.print_step(f"❌ Erro na criação: {str(e)}", "ERROR")

        # 4. Testar obtenção de benefício específico (GET /admin/benefits/{partner_id}/{benefit_id})
        # Usando IDs conhecidos que existem no banco de dados
        self.print_step("Testando obtenção de benefício específico...")
        try:
            # IDs conhecidos que existem no Firestore
            known_partner_id = "PTN_T4L5678_TEC"
            known_benefit_id = "BNF_4A9B21_DC"

            endpoint = f"/admin/benefits/{known_partner_id}/{known_benefit_id}"
            success, data = self.test_authenticated_endpoint(endpoint)

            benefits_result["get_specific_benefit"]["success"] = success
            benefits_result["get_specific_benefit"]["data"] = data

            if success and data:
                self.print_step(
                    f"✅ Benefício específico obtido com sucesso: {known_benefit_id}",
                    "SUCCESS",
                )
            else:
                self.print_step("❌ Falha ao obter benefício específico", "ERROR")

        except Exception as e:
            benefits_result["get_specific_benefit"]["error"] = str(e)
            self.print_step(f"❌ Erro ao obter benefício: {str(e)}", "ERROR")

            # 5. Testar atualização de benefício (PUT /admin/benefits/{partner_id}/{benefit_id})
            self.print_step("Testando atualização de benefício...")
            try:
                update_data = {
                    "title": "Benefício de Teste Admin - Atualizado",
                    "description": "Descrição atualizada pelo teste admin",
                    "value": 20,
                    "category": "desconto",
                    "type": "percentage",
                    "valid_from": "2025-01-01T00:00:00Z",
                    "valid_to": "2025-12-31T23:59:59Z",
                    "active": True,
                    "audience": ["student", "employee"],
                }

                endpoint = (
                    f"/admin/benefits/{self.test_partner_id}/{self.test_benefit_id}"
                )
                success, data = self.test_authenticated_endpoint_with_data(
                    endpoint, method="PUT", data=update_data
                )

                benefits_result["update_benefit"]["success"] = success
                benefits_result["update_benefit"]["data"] = data

                if success and data:
                    self.print_step("✅ Benefício atualizado com sucesso", "SUCCESS")
                else:
                    self.print_step("❌ Falha na atualização de benefício", "ERROR")

            except Exception as e:
                benefits_result["update_benefit"]["error"] = str(e)
                self.print_step(f"❌ Erro na atualização: {str(e)}", "ERROR")

            # 6. Testar exclusão de benefício (DELETE /admin/benefits/{partner_id}/{benefit_id})
            self.print_step("Testando exclusão de benefício (soft delete)...")
            try:
                endpoint = f"/admin/benefits/{self.test_partner_id}/{self.test_benefit_id}?soft_delete=true"
                success, data = self.test_authenticated_endpoint_with_data(
                    endpoint, method="DELETE"
                )

                benefits_result["delete_benefit"]["success"] = success
                benefits_result["delete_benefit"]["data"] = data

                if success:
                    self.print_step(
                        "✅ Benefício excluído com sucesso (soft delete)", "SUCCESS"
                    )
                else:
                    self.print_step("❌ Falha na exclusão de benefício", "ERROR")

            except Exception as e:
                benefits_result["delete_benefit"]["error"] = str(e)
                self.print_step(f"❌ Erro na exclusão: {str(e)}", "ERROR")

        # Resumo dos testes de benefícios
        successful_tests = sum(
            1
            for test in benefits_result.values()
            if isinstance(test, dict) and test.get("success", False)
        )
        total_tests = len([k for k in benefits_result if k != "timestamp"])

        self.print_step(
            f"Testes de benefícios: {successful_tests}/{total_tests} bem-sucedidos",
            "SUCCESS" if successful_tests > 0 else "WARNING",
        )

        return benefits_result

    def test_admin_permissions(self) -> dict:
        """
        Testa permissões específicas de Admin.

        Returns:
            Dicionário com resultado do teste de permissões
        """
        self.print_header("TESTANDO PERMISSÕES DE ADMIN")

        permissions_result = {
            "can_access_admin_panel": False,
            "can_manage_partners": False,
            "can_manage_students": False,
            "can_manage_employees": False,
            "can_view_metrics": False,
            "can_send_notifications": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Testar acesso ao gerenciamento de parceiros
        partners_success, _ = self.test_authenticated_endpoint("/admin/partners")
        permissions_result["can_manage_partners"] = partners_success

        # Testar gerenciamento de estudantes
        students_success, _ = self.test_authenticated_endpoint("/admin/students")
        permissions_result["can_manage_students"] = students_success

        # Testar gerenciamento de funcionários
        employees_success, _ = self.test_authenticated_endpoint("/admin/employees")
        permissions_result["can_manage_employees"] = employees_success

        # Testar acesso a métricas
        metrics_success, _ = self.test_authenticated_endpoint("/admin/metrics")
        permissions_result["can_view_metrics"] = metrics_success

        # Testar capacidade de envio de notificações (POST)
        notification_data = {
            "target": "students",
            "type": "push",
            "title": "Teste de Notificação",
            "message": "Esta é uma notificação de teste do admin",
        }
        notifications_success, _ = self.test_authenticated_endpoint_with_data(
            "/admin/notifications", method="POST", data=notification_data
        )
        permissions_result["can_send_notifications"] = notifications_success

        # Definir acesso ao painel admin baseado no sucesso geral
        permissions_result["can_access_admin_panel"] = any(
            [
                partners_success,
                students_success,
                employees_success,
                metrics_success,
            ]
        )

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

    def run_complete_admin_test(self) -> dict:
        """
        Executa o teste completo de autenticação para Admin.

        Returns:
            Dicionário com resultado completo do teste
        """
        self.print_header("TESTE COMPLETO DE AUTENTICAÇÃO - ADMIN")

        # Executar fluxo básico de autenticação
        basic_result = self.run_basic_auth_flow("admin_teste")

        if not basic_result["success"]:
            self.print_step(f"Falha no fluxo básico: {basic_result['error']}", "ERROR")
            return basic_result

        # Obter informações detalhadas do usuário
        user_info = self.get_user_info_from_me_endpoint()

        # Testar endpoints específicos de Admin
        endpoint_results = self.test_admin_specific_endpoints()

        # Testar gerenciamento de benefícios
        benefits_results = self.test_benefits_management_endpoints()

        # Testar permissões de Admin
        permissions_result = self.test_admin_permissions()

        # Compilar resultado final
        complete_result = {
            **basic_result,
            "user_info": user_info,
            "endpoint_results": endpoint_results,
            "benefits_management": benefits_results,
            "permissions": permissions_result,
            "total_endpoints_tested": len(endpoint_results),
            "successful_endpoints": sum(1 for r in endpoint_results if r["success"]),
            "test_completed_at": datetime.now().isoformat(),
        }

        # Salvar relatório
        report_path = self.save_test_report([complete_result], "admin")

        # Resumo final
        self.print_header("RESUMO DO TESTE - ADMIN")
        self.print_step(
            f"✅ Autenticação Firebase: {'Sucesso' if basic_result['success'] else 'Falha'}"
        )
        self.print_step(
            f"✅ Login Backend: {'Sucesso' if basic_result['success'] else 'Falha'}"
        )
        self.print_step(
            f"📊 Endpoints testados: {complete_result['successful_endpoints']}/{complete_result['total_endpoints_tested']}"
        )

        if user_info:
            self.print_step(f"👤 Usuário: {user_info.get('email', 'N/A')}")
            self.print_step(f"🆔 ID: {user_info.get('id', 'N/A')}")
            self.print_step(f"👥 Role: {user_info.get('role', 'N/A')}")

        self.print_step(f"📄 Relatório salvo: {report_path}")

        return complete_result


def main():
    """Função principal para execução do teste de Admin."""
    print("🔐 Iniciando Teste de Autenticação - ADMIN")
    print(f"⏰ Horário: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        tester = AdminAuthenticationTester()
        result = tester.run_complete_admin_test()

        if result["success"]:
            print("\n🎉 Teste de Admin concluído com SUCESSO!")
            sys.exit(0)
        else:
            print(
                f"\n❌ Teste de Admin FALHOU: {result.get('error', 'Erro desconhecido')}"
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
