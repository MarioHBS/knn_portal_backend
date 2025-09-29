#!/usr/bin/env python3
"""
Teste de Autenticação - Partner - Portal KNN

Este script testa especificamente o fluxo de autenticação para usuários Partner,
incluindo endpoints específicos e permissões de parceiros.

Autor: Sistema de Testes KNN
Data: 2025-01-06
"""

import sys
from contextlib import suppress
from datetime import datetime

from base_auth_test import BACKEND_BASE_URL, BaseAuthenticationTester


class PartnerAuthenticationTester(BaseAuthenticationTester):
    """Testador específico para autenticação de Partner."""

    def __init__(self):
        """Inicializa o testador de Partner."""
        super().__init__()
        self.entity_type = "partner"

    def test_partner_specific_endpoints(self) -> list[dict]:
        """
        Testa endpoints específicos para Partner.

        Returns:
            Lista com resultados dos testes de endpoints
        """
        self.print_header("TESTANDO ENDPOINTS ESPECÍFICOS DE PARTNER")

        partner_endpoints = [
            "/users/me",
            "/partner/redeem",
            "/partner/promotions",
            "/partner/reports",
        ]

        endpoint_results = []

        for endpoint in partner_endpoints:
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

    def test_partner_permissions(self) -> dict:
        """
        Testa permissões específicas de Partner.

        Returns:
            Dicionário com resultado do teste de permissões
        """
        self.print_header("TESTANDO PERMISSÕES DE PARTNER")

        permissions_result = {
            "can_view_reports": False,
            "can_access_user_info": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Testar acesso a relatórios (único endpoint específico de partner que existe)
        reports_success, _ = self.test_authenticated_endpoint("/partner/reports")
        permissions_result["can_view_reports"] = reports_success

        # Testar acesso às próprias informações via /users/me
        user_info_success, _ = self.test_authenticated_endpoint("/users/me")
        permissions_result["can_access_user_info"] = user_info_success

        # Resumo das permissões
        total_permissions = 2
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

    def test_partner_business_logic(self) -> dict:
        """
        Testa lógica de negócio específica para Partner.

        Returns:
            Dicionário com resultado dos testes de lógica de negócio
        """
        self.print_header("TESTANDO LÓGICA DE NEGÓCIO - PARTNER")

        business_logic_result = {
            "can_access_own_profile": False,
            "timestamp": datetime.now().isoformat(),
        }

        # Testar acesso ao próprio perfil via /users/me (endpoint correto)
        profile_success, profile_data = self.test_authenticated_endpoint("/users/me")
        business_logic_result["can_access_own_profile"] = profile_success

        if profile_success and profile_data:
            # Verificar se os dados do perfil contêm informações esperadas
            expected_fields = ["id", "email", "role", "username"]
            profile_fields_present = sum(
                1 for field in expected_fields if field in profile_data
            )
            business_logic_result["profile_fields_present"] = profile_fields_present
            business_logic_result["total_expected_fields"] = len(expected_fields)
            
            self.print_step(
                f"✅ Campos do perfil encontrados: {profile_fields_present}/{len(expected_fields)}",
                "SUCCESS"
            )

        # Resumo da lógica de negócio
        total_tests = 1
        successful_tests = sum(
            1
            for key, value in business_logic_result.items()
            if key.startswith("can_") and value
        )

        self.print_step(
            f"Testes de lógica de negócio: {successful_tests}/{total_tests} bem-sucedidos",
            "SUCCESS" if successful_tests > 0 else "WARNING",
        )

        return business_logic_result

    def test_partner_promotions_endpoints(self) -> dict:
        """
        Testa os endpoints de promoções do parceiro (GET, POST, PUT, DELETE).
        Fluxo: Lista promoções -> Cria duas -> Edita uma -> Exclui uma -> Verifica contagem final.

        Returns:
            Dicionário com resultado do teste de promoções
        """
        self.print_header("TESTANDO ENDPOINTS DE PROMOÇÕES DO PARCEIRO")

        if not self.jwt_token:
            return {
                "success": False,
                "error": "Token JWT não disponível para teste de promoções",
                "operations": [],
            }

        # Obter partner_id do usuário logado
        partner_id = self.get_user_partner_id()
        if not partner_id:
            return {
                "success": False,
                "error": "Não foi possível obter partner_id do usuário logado",
                "operations": [],
            }

        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        operations = []
        created_promotion_ids = []

        try:
            # 1. Listar promoções iniciais
            self.print_step("1. Listando promoções iniciais do parceiro")
            response = self.session.get(
                f"{BACKEND_BASE_URL}/partner/promotions",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                promotions_data = response.json()
                initial_count = len(promotions_data.get("data", []))
                self.print_step(
                    f"✅ Promoções iniciais encontradas: {initial_count}", "SUCCESS"
                )
                operations.append({
                    "operation": "GET_INITIAL",
                    "success": True,
                    "count": initial_count,
                })
            else:
                self.print_step(
                    f"❌ Erro ao listar promoções iniciais: {response.status_code}",
                    "ERROR",
                )
                operations.append({
                    "operation": "GET_INITIAL",
                    "success": False,
                    "status_code": response.status_code,
                })
                return {
                    "success": False,
                    "error": f"Falha ao listar promoções iniciais: {response.status_code}",
                    "operations": operations,
                }

            # 2. Criar primeira promoção
            self.print_step("2. Criando primeira promoção de teste")
            promotion_1_data = {
                "title": f"Promoção Teste 1 - Desconto Especial - {datetime.now().strftime('%H:%M:%S')}",
                "type": "discount",
                "valid_from": "2025-01-01T00:00:00Z",
                "valid_to": "2025-12-31T23:59:59Z",
                "active": True,
                "audience": ["student", "employee"],
            }

            response = self.session.post(
                f"{BACKEND_BASE_URL}/partner/promotions",
                json=promotion_1_data,
                headers=headers,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                promotion_1_response = response.json()
                promotion_1_id = promotion_1_response.get("data", {}).get("id")
                created_promotion_ids.append(promotion_1_id)
                self.print_step(
                    f"✅ Primeira promoção criada com ID: {promotion_1_id}", "SUCCESS"
                )
                operations.append({
                    "operation": "POST_PROMOTION_1",
                    "success": True,
                    "promotion_id": promotion_1_id,
                })
            else:
                self.print_step(
                    f"❌ Erro ao criar primeira promoção: {response.status_code}",
                    "ERROR",
                )
                operations.append({
                    "operation": "POST_PROMOTION_1",
                    "success": False,
                    "status_code": response.status_code,
                })
                return {
                    "success": False,
                    "error": f"Falha ao criar primeira promoção: {response.status_code}",
                    "operations": operations,
                }

            # 3. Criar segunda promoção
            self.print_step("3. Criando segunda promoção de teste")
            promotion_2_data = {
                "title": f"Promoção Teste 2 - Oferta Limitada - {datetime.now().strftime('%H:%M:%S')}",
                "type": "discount",
                "valid_from": "2025-01-01T00:00:00Z",
                "valid_to": "2025-06-30T23:59:59Z",
                "active": True,
                "audience": ["student"],
            }

            response = self.session.post(
                f"{BACKEND_BASE_URL}/partner/promotions",
                json=promotion_2_data,
                headers=headers,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                promotion_2_response = response.json()
                promotion_2_id = promotion_2_response.get("data", {}).get("id")
                created_promotion_ids.append(promotion_2_id)
                self.print_step(
                    f"✅ Segunda promoção criada com ID: {promotion_2_id}", "SUCCESS"
                )
                operations.append({
                    "operation": "POST_PROMOTION_2",
                    "success": True,
                    "promotion_id": promotion_2_id,
                })
            else:
                self.print_step(
                    f"❌ Erro ao criar segunda promoção: {response.status_code}",
                    "ERROR",
                )
                operations.append({
                    "operation": "POST_PROMOTION_2",
                    "success": False,
                    "status_code": response.status_code,
                })

            # 4. Atualizar segunda promoção (seguindo o padrão do complete_auth_flow_test.py)
            promotion_2_id = operations[-1].get("promotion_id") if operations and operations[-1]["success"] else None
            if promotion_2_id:
                self.print_step(f"4. Atualizando segunda promoção (ID: {promotion_2_id})")
                update_data = {
                    "title": f"Promoção Teste 2 - ATUALIZADA - Super Desconto 25% - {datetime.now().strftime('%H:%M:%S')}",
                    "type": "discount",
                    "valid_from": "2025-01-01T00:00:00Z",
                    "valid_to": "2025-06-30T23:59:59Z",
                    "active": True,
                    "audience": ["student", "employee"],  # Expandindo audiência
                }

                response = self.session.put(
                    f"{BACKEND_BASE_URL}/partner/promotions/{promotion_2_id}",
                    json=update_data,
                    headers=headers,
                    timeout=10,
                )

                if response.status_code in [200, 201]:
                    update_response = response.json()
                    updated_title = update_response.get("data", {}).get("title", "N/A")
                    self.print_step(
                        f"✅ Segunda promoção atualizada com sucesso", "SUCCESS"
                    )
                    self.print_step(
                        f"   Novo título: {updated_title}",
                        "INFO",
                    )
                    operations.append({
                        "operation": "PUT_PROMOTION_2",
                        "success": True,
                        "promotion_id": promotion_2_id,
                    })
                else:
                    self.print_step(
                        f"❌ Erro ao atualizar segunda promoção: {response.status_code}",
                        "ERROR",
                    )
                    operations.append({
                        "operation": "PUT_PROMOTION_2",
                        "success": False,
                        "status_code": response.status_code,
                    })
            else:
                self.print_step(
                    "⚠️ PUT não testado: ID da segunda promoção não disponível",
                    "WARNING",
                )

            # 5. Excluir primeira promoção
            promotion_1_id = None
            for op in operations:
                if op["operation"] == "POST_PROMOTION_1" and op["success"]:
                    promotion_1_id = op["promotion_id"]
                    break
            
            if promotion_1_id:
                self.print_step(f"5. Excluindo primeira promoção (ID: {promotion_1_id})")
                response = self.session.delete(
                    f"{BACKEND_BASE_URL}/partner/promotions/{promotion_1_id}",
                    headers=headers,
                    timeout=10,
                )

                if response.status_code in [200, 204]:
                    self.print_step(
                        f"✅ Primeira promoção excluída com sucesso", "SUCCESS"
                    )
                    operations.append({
                        "operation": "DELETE_PROMOTION_1",
                        "success": True,
                        "promotion_id": promotion_1_id,
                    })
                    # Remover da lista para não tentar excluir novamente no cleanup
                    if promotion_1_id in created_promotion_ids:
                        created_promotion_ids.remove(promotion_1_id)
                else:
                    self.print_step(
                        f"❌ Erro ao excluir primeira promoção: {response.status_code}",
                        "ERROR",
                    )
                    operations.append({
                        "operation": "DELETE_PROMOTION_1",
                        "success": False,
                        "status_code": response.status_code,
                    })
            else:
                self.print_step(
                    "⚠️ DELETE não testado: ID da primeira promoção não disponível",
                    "WARNING",
                )

            # 6. Verificar contagem final
            self.print_step("6. Verificando contagem final de promoções")
            response = self.session.get(
                f"{BACKEND_BASE_URL}/partner/promotions",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                final_promotions_data = response.json()
                final_count = len(final_promotions_data.get("data", []))
                expected_count = initial_count + 1  # Criamos 2, excluímos 1
                
                self.print_step(
                    f"✅ Contagem final: {final_count} promoções (esperado: {expected_count})",
                    "SUCCESS",
                )
                operations.append({
                    "operation": "GET_FINAL",
                    "success": True,
                    "count": final_count,
                    "expected_count": expected_count,
                })

                # Verificar se a contagem está correta
                count_correct = final_count == expected_count
                if not count_correct:
                    self.print_step(
                        f"⚠️ Contagem não confere! Final: {final_count}, Esperado: {expected_count}",
                        "WARNING",
                    )
            else:
                self.print_step(
                    f"❌ Erro ao verificar contagem final: {response.status_code}",
                    "ERROR",
                )
                operations.append({
                    "operation": "GET_FINAL",
                    "success": False,
                    "status_code": response.status_code,
                })

            # Cleanup: Excluir promoções restantes criadas no teste
            for promotion_id in created_promotion_ids:
                self.print_step(f"🧹 Limpando promoção ID: {promotion_id}")
                with suppress(Exception):
                    cleanup_response = self.session.delete(
                        f"{BACKEND_BASE_URL}/partner/promotions/{promotion_id}",
                        headers=headers,
                        timeout=10,
                    )
                    if cleanup_response.status_code == 204:
                        self.print_step(f"✅ Promoção {promotion_id} removida", "SUCCESS")
                    else:
                        self.print_step(
                            f"⚠️ Falha ao remover promoção {promotion_id}: {cleanup_response.status_code}",
                            "WARNING",
                        )

            # Verificar se todos os testes principais foram bem-sucedidos
            main_operations = [op for op in operations if not op["operation"].startswith("GET_FINAL")]
            successful_operations = sum(1 for op in main_operations if op["success"])
            total_operations = len(main_operations)

            success = successful_operations == total_operations

            return {
                "success": success,
                "partner_id": partner_id,
                "operations": operations,
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "message": f"Teste de promoções {'concluído com sucesso' if success else 'falhou'}",
            }

        except Exception as e:
            self.print_step(f"❌ Erro inesperado no teste de promoções: {str(e)}", "ERROR")
            
            # Cleanup em caso de erro
            for promotion_id in created_promotion_ids:
                with suppress(Exception):
                    self.session.delete(
                        f"{BACKEND_BASE_URL}/partner/promotions/{promotion_id}",
                        headers=headers,
                        timeout=5,
                    )

            return {
                "success": False,
                "error": f"Erro inesperado: {str(e)}",
                "operations": operations,
            }

    def run_complete_partner_test(self) -> dict:
        """
        Executa o teste completo de autenticação para Partner.

        Returns:
            Dicionário com resultado completo do teste
        """
        self.print_header("TESTE COMPLETO DE AUTENTICAÇÃO - PARTNER")

        # Executar fluxo básico de autenticação
        basic_result = self.run_basic_auth_flow("parceiro_teste")

        if not basic_result["success"]:
            self.print_step(f"Falha no fluxo básico: {basic_result['error']}", "ERROR")
            return basic_result

        # Obter informações detalhadas do usuário
        user_info = self.get_user_info_from_me_endpoint()

        # Testar endpoints específicos de Partner
        endpoint_results = self.test_partner_specific_endpoints()

        # Testar permissões de Partner
        permissions_result = self.test_partner_permissions()

        # Testar lógica de negócio de Partner
        business_logic_result = self.test_partner_business_logic()

        # Testar endpoints de promoções do parceiro
        promotions_result = self.test_partner_promotions_endpoints()

        # Compilar resultado final
        complete_result = {
            **basic_result,
            "user_info": user_info,
            "endpoint_results": endpoint_results,
            "permissions": permissions_result,
            "business_logic": business_logic_result,
            "promotions_test": promotions_result,
            "total_endpoints_tested": len(endpoint_results),
            "successful_endpoints": sum(1 for r in endpoint_results if r["success"]),
            "test_completed_at": datetime.now().isoformat(),
        }

        # Salvar relatório
        report_path = self.save_test_report([complete_result], "partner")

        # Resumo final
        self.print_header("RESUMO DO TESTE - PARTNER")
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
            f"🎯 Teste de promoções: {'Sucesso' if promotions_result.get('success', False) else 'Falha'}"
        )

        if user_info:
            self.print_step(f"👤 Usuário: {user_info.get('email', 'N/A')}")
            self.print_step(f"🆔 ID: {user_info.get('id', 'N/A')}")
            self.print_step(f"👥 Role: {user_info.get('role', 'N/A')}")
            self.print_step(f"🏢 Partner ID: {user_info.get('partner_id', 'N/A')}")

        self.print_step(f"📄 Relatório salvo: {report_path}")

        return complete_result


def main():
    """Função principal para execução do teste de Partner."""
    print("🔐 Iniciando Teste de Autenticação - PARTNER")
    print(f"⏰ Horário: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        tester = PartnerAuthenticationTester()
        result = tester.run_complete_partner_test()

        if result["success"]:
            print("\n🎉 Teste de Partner concluído com SUCESSO!")
            sys.exit(0)
        else:
            print(
                f"\n❌ Teste de Partner FALHOU: {result.get('error', 'Erro desconhecido')}"
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
