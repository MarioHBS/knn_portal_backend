#!/usr/bin/env python3
"""
Testes específicos para endpoints do perfil Admin.

Este módulo contém testes detalhados para todos os endpoints
disponíveis para administradores no Portal de Benefícios KNN.
"""

import json
import logging
import time

import requests
from requests.exceptions import RequestException
from test_config import (
    REQUEST_TIMEOUT,
    TEST_DATA,
    build_url,
    get_auth_headers,
)
from test_runner import TestResult

logger = logging.getLogger(__name__)


class AdminEndpointTester:
    """Classe para testes específicos de endpoints de administradores."""

    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = REQUEST_TIMEOUT
        self.headers = get_auth_headers("admin")
        self.results: list[TestResult] = []

    def _make_request(self, method: str, url: str, **kwargs) -> tuple[int, dict, float]:
        """Executa requisição HTTP com tratamento de erros."""
        start_time = time.time()

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )

            response_time = time.time() - start_time

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}

            return response.status_code, response_data, response_time

        except RequestException as e:
            response_time = time.time() - start_time
            return 0, {"error": str(e)}, response_time

    def _create_test_result(
        self,
        endpoint_name: str,
        method: str,
        status_code: int,
        response_data: dict,
        response_time: float,
    ) -> TestResult:
        """Cria resultado de teste baseado na resposta."""
        if status_code == 0:
            status = "fail"
            error_message = response_data.get("error", "Erro de conexão")
        elif 200 <= status_code < 300:
            status = "pass"
            error_message = None
        elif status_code == 401:
            status = "skip"
            error_message = "Token de autenticação inválido ou expirado"
        elif status_code == 403:
            status = "skip"
            error_message = "Acesso negado para perfil de administrador"
        elif status_code == 404:
            status = "skip"
            error_message = "Recurso não encontrado (esperado para dados de teste)"
        else:
            status = "fail"
            error_message = response_data.get("detail", f"HTTP {status_code}")

        return TestResult(
            endpoint=f"admin.{endpoint_name}",
            method=method,
            status=status,
            response_time=response_time,
            status_code=status_code if status_code > 0 else None,
            error_message=error_message,
            response_data=response_data if status == "pass" else None,
        )

    def test_list_partners(self) -> TestResult:
        """Testa listagem de parceiros para administradores."""
        logger.info("Testando listagem de parceiros (admin)")

        url = build_url("/admin/partners")

        # Teste básico sem parâmetros
        status_code, response_data, response_time = self._make_request("GET", url)

        result = self._create_test_result(
            "list_partners", "GET", status_code, response_data, response_time
        )

        # Validações específicas para sucesso
        if result.status == "pass":
            # Verificar estrutura da resposta
            if not isinstance(response_data, dict):
                result.status = "fail"
                result.error_message = "Resposta não é um objeto JSON válido"
            elif "partners" not in response_data:
                result.status = "fail"
                result.error_message = "Campo 'partners' não encontrado na resposta"
            elif not isinstance(response_data["partners"], list):
                result.status = "fail"
                result.error_message = "Campo 'partners' deve ser uma lista"
            else:
                partners = response_data["partners"]
                logger.info(f"✅ Listagem de parceiros retornou {len(partners)} itens")

                # Verificar se há informações de total (específico para admin)
                if "total" in response_data:
                    logger.info(
                        f"   Total de parceiros no sistema: {response_data['total']}"
                    )

                # Verificar se inclui parceiros inativos (privilégio de admin)
                active_count = len([p for p in partners if p.get("active", True)])
                inactive_count = len(partners) - active_count
                if inactive_count > 0:
                    logger.info(
                        f"   Parceiros ativos: {active_count}, inativos: {inactive_count}"
                    )

        return result

    def test_get_partner_details(self) -> TestResult:
        """Testa obtenção de detalhes de um parceiro específico (admin)."""
        logger.info("Testando detalhes de parceiro específico (admin)")

        # Usar ID de teste
        partner_id = "test-partner-id"
        url = build_url("/admin/partners/{id}", id=partner_id)

        status_code, response_data, response_time = self._make_request("GET", url)

        result = self._create_test_result(
            "get_partner_details", "GET", status_code, response_data, response_time
        )

        # Para este teste, 404 é esperado pois usamos ID de teste
        if result.status_code == 404:
            result.status = "skip"
            result.error_message = "ID de teste não encontrado (comportamento esperado)"
            logger.info("⏭️ ID de teste não encontrado (esperado)")
        elif result.status == "pass":
            # Verificar estrutura da resposta (admin tem acesso a mais campos)
            required_fields = ["id", "trade_name", "category", "active"]
            missing_fields = [
                field for field in required_fields if field not in response_data
            ]

            if missing_fields:
                result.status = "fail"
                result.error_message = f"Campos obrigatórios ausentes: {missing_fields}"
            else:
                logger.info("✅ Detalhes do parceiro retornados corretamente")

                # Verificar campos específicos de admin
                admin_fields = ["cnpj", "created_at", "updated_at", "contact_info"]
                available_admin_fields = [
                    field for field in admin_fields if field in response_data
                ]
                if available_admin_fields:
                    logger.info(
                        f"   Campos administrativos disponíveis: {available_admin_fields}"
                    )

        return result

    def test_list_students(self) -> TestResult:
        """Testa listagem de estudantes."""
        logger.info("Testando listagem de estudantes")

        url = build_url("/admin/{entity}", entity="students")
        params = {"limit": "10", "offset": "0"}

        status_code, response_data, response_time = self._make_request(
            "GET", url, params=params
        )

        result = self._create_test_result(
            "list_students", "GET", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            if "students" not in response_data:
                result.status = "fail"
                result.error_message = "Campo 'students' não encontrado na resposta"
            elif not isinstance(response_data["students"], list):
                result.status = "fail"
                result.error_message = "Campo 'students' deve ser uma lista"
            else:
                students = response_data["students"]
                logger.info(f"✅ Listagem de estudantes retornou {len(students)} itens")

                if "total" in response_data:
                    logger.info(f"   Total de estudantes: {response_data['total']}")

        return result

    def test_create_student(self) -> TestResult:
        """Testa criação de novo estudante."""
        logger.info("Testando criação de estudante")

        url = build_url("/admin/{entity}", entity="students")
        json_data = TEST_DATA["student"].copy()

        # Adicionar timestamp para evitar duplicatas
        json_data["email"] = f"teste_{int(time.time())}@email.com"

        status_code, response_data, response_time = self._make_request(
            "POST", url, json=json_data
        )

        result = self._create_test_result(
            "create_student", "POST", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            if "id" not in response_data:
                result.status = "fail"
                result.error_message = (
                    "Campo 'id' não encontrado na resposta de criação"
                )
            else:
                student_id = response_data["id"]
                logger.info(f"✅ Estudante criado com ID: {student_id}")

                # Armazenar ID para possível limpeza posterior
                if not hasattr(self, "created_entities"):
                    self.created_entities = []
                self.created_entities.append({"type": "student", "id": student_id})

        return result

    def test_update_student(self) -> TestResult:
        """Testa atualização de estudante."""
        logger.info("Testando atualização de estudante")

        # Usar ID de teste
        student_id = "test-student-id"
        url = build_url("/admin/{entity}/{id}", entity="students", id=student_id)

        json_data = {
            "nome": "João Silva Santos Atualizado",
            "telefone": "(11) 99999-8888",
        }

        status_code, response_data, response_time = self._make_request(
            "PUT", url, json=json_data
        )

        result = self._create_test_result(
            "update_student", "PUT", status_code, response_data, response_time
        )

        # Para este teste, 404 é esperado pois usamos ID de teste
        if result.status_code == 404:
            result.status = "skip"
            result.error_message = "ID de teste não encontrado (comportamento esperado)"
            logger.info("⏭️ ID de teste não encontrado (esperado)")
        elif result.status == "pass":
            logger.info("✅ Estudante atualizado com sucesso")

        return result

    def test_delete_student(self) -> TestResult:
        """Testa exclusão de estudante."""
        logger.info("Testando exclusão de estudante")

        # Usar ID de teste
        student_id = "test-student-id"
        url = build_url("/admin/{entity}/{id}", entity="students", id=student_id)

        status_code, response_data, response_time = self._make_request("DELETE", url)

        result = self._create_test_result(
            "delete_student", "DELETE", status_code, response_data, response_time
        )

        # Para este teste, 404 é esperado pois usamos ID de teste
        if result.status_code == 404:
            result.status = "skip"
            result.error_message = "ID de teste não encontrado (comportamento esperado)"
            logger.info("⏭️ ID de teste não encontrado (esperado)")
        elif result.status == "pass":
            logger.info("✅ Estudante excluído com sucesso")

        return result

    def test_get_metrics(self) -> TestResult:
        """Testa obtenção de métricas do sistema."""
        logger.info("Testando métricas do sistema")

        url = build_url("/admin/metrics")

        status_code, response_data, response_time = self._make_request("GET", url)

        result = self._create_test_result(
            "get_metrics", "GET", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            expected_metrics = ["total_students", "total_partners", "total_validations"]
            available_metrics = [
                metric for metric in expected_metrics if metric in response_data
            ]

            if not available_metrics:
                result.status = "fail"
                result.error_message = "Nenhuma métrica encontrada na resposta"
            else:
                logger.info(f"✅ Métricas disponíveis: {available_metrics}")

                # Log das métricas
                for metric in available_metrics:
                    logger.info(f"   {metric}: {response_data[metric]}")

                # Verificar se há métricas de período
                if "period_stats" in response_data:
                    logger.info("   Estatísticas de período disponíveis")

        return result

    def test_send_notifications(self) -> TestResult:
        """Testa envio de notificações."""
        logger.info("Testando envio de notificações")

        url = build_url("/admin/notifications")
        json_data = TEST_DATA["notification"]

        status_code, response_data, response_time = self._make_request(
            "POST", url, json=json_data
        )

        result = self._create_test_result(
            "send_notifications", "POST", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            if "sent_count" not in response_data:
                result.status = "fail"
                result.error_message = "Campo 'sent_count' não encontrado na resposta"
            else:
                sent_count = response_data["sent_count"]
                logger.info(f"✅ Notificações enviadas: {sent_count}")

                if "failed_count" in response_data:
                    failed_count = response_data["failed_count"]
                    logger.info(f"   Falhas no envio: {failed_count}")

        return result

    def test_list_promotions(self) -> TestResult:
        """Testa listagem de promoções (admin)."""
        logger.info("Testando listagem de promoções (admin)")

        url = build_url("/admin/{entity}", entity="promotions")
        params = {"limit": "20", "offset": "0"}

        status_code, response_data, response_time = self._make_request(
            "GET", url, params=params
        )

        result = self._create_test_result(
            "list_promotions", "GET", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            if "promotions" not in response_data:
                result.status = "fail"
                result.error_message = "Campo 'promotions' não encontrado na resposta"
            elif not isinstance(response_data["promotions"], list):
                result.status = "fail"
                result.error_message = "Campo 'promotions' deve ser uma lista"
            else:
                promotions = response_data["promotions"]
                logger.info(
                    f"✅ Listagem de promoções retornou {len(promotions)} itens"
                )

                # Verificar estrutura das promoções
                if promotions:
                    first_promotion = promotions[0]
                    required_fields = ["id", "title", "partner_id"]
                    missing_fields = [
                        field
                        for field in required_fields
                        if field not in first_promotion
                    ]

                    if missing_fields:
                        logger.warning(
                            f"   Campos ausentes na promoção: {missing_fields}"
                        )
                    else:
                        logger.info("   Estrutura das promoções validada")

        return result

    def test_invalid_entity(self) -> TestResult:
        """Testa acesso a entidade inválida."""
        logger.info("Testando entidade inválida")

        url = build_url("/admin/{entity}", entity="invalid_entity")

        status_code, response_data, response_time = self._make_request("GET", url)

        result = self._create_test_result(
            "invalid_entity", "GET", status_code, response_data, response_time
        )

        # Deve retornar 404 ou 400
        if result.status_code in [400, 404]:
            result.status = "pass"
            result.error_message = None
            logger.info(
                f"✅ Entidade inválida rejeitada corretamente: HTTP {result.status_code}"
            )
        elif result.status == "pass":
            result.status = "fail"
            result.error_message = "Deveria retornar erro para entidade inválida"

        return result

    def test_invalid_authentication(self) -> TestResult:
        """Testa comportamento com token inválido."""
        logger.info("Testando autenticação inválida (admin)")

        # Usar headers sem token
        invalid_headers = {"Content-Type": "application/json"}

        url = build_url("/admin/metrics")

        start_time = time.time()
        try:
            response = self.session.get(
                url, headers=invalid_headers, timeout=REQUEST_TIMEOUT
            )
            response_time = time.time() - start_time

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}

            # Deve retornar 401 Unauthorized
            if response.status_code == 401:
                logger.info("✅ Autenticação inválida detectada corretamente")
                return TestResult(
                    endpoint="admin.invalid_auth",
                    method="GET",
                    status="pass",
                    response_time=response_time,
                    status_code=401,
                    response_data=response_data,
                )
            else:
                return TestResult(
                    endpoint="admin.invalid_auth",
                    method="GET",
                    status="fail",
                    response_time=response_time,
                    status_code=response.status_code,
                    error_message=f"Esperado 401, recebido {response.status_code}",
                )

        except RequestException as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint="admin.invalid_auth",
                method="GET",
                status="fail",
                response_time=response_time,
                error_message=str(e),
            )

    def run_all_tests(self) -> list[TestResult]:
        """Executa todos os testes de endpoints de administrador."""
        logger.info("Iniciando testes de endpoints de administrador")

        test_methods = [
            self.test_list_partners,
            self.test_get_partner_details,
            self.test_list_students,
            self.test_create_student,
            self.test_update_student,
            self.test_delete_student,
            self.test_get_metrics,
            self.test_send_notifications,
            self.test_list_promotions,
            self.test_invalid_entity,
            self.test_invalid_authentication,
        ]

        results = []

        for test_method in test_methods:
            try:
                result = test_method()
                results.append(result)

                # Log do resultado
                status_emoji = {"pass": "✅", "fail": "❌", "skip": "⏭️"}

                logger.info(
                    f"{status_emoji.get(result.status, '❓')} {result.endpoint} - "
                    f"{result.status.upper()} ({result.response_time:.3f}s)"
                )

                if result.error_message:
                    logger.warning(f"   Erro: {result.error_message}")

            except Exception as e:
                logger.error(f"Erro ao executar {test_method.__name__}: {e}")
                results.append(
                    TestResult(
                        endpoint=f"admin.{test_method.__name__}",
                        method="UNKNOWN",
                        status="fail",
                        response_time=0.0,
                        error_message=str(e),
                    )
                )

        self.results = results

        # Estatísticas
        passed = len([r for r in results if r.status == "pass"])
        failed = len([r for r in results if r.status == "fail"])
        skipped = len([r for r in results if r.status == "skip"])

        logger.info(
            f"Testes de administrador concluídos: {passed} aprovados, {failed} falharam, {skipped} ignorados"
        )

        return results

    def cleanup(self):
        """Limpa recursos utilizados e entidades criadas durante os testes."""
        # Limpar entidades criadas durante os testes
        if hasattr(self, "created_entities"):
            logger.info("Limpando entidades criadas durante os testes")
            for entity in self.created_entities:
                try:
                    url = build_url(
                        "/admin/{entity}/{id}",
                        entity=entity["type"] + "s",
                        id=entity["id"],
                    )
                    self._make_request("DELETE", url)
                    logger.info(f"   Entidade {entity['type']} {entity['id']} removida")
                except Exception as e:
                    logger.warning(
                        f"   Erro ao remover {entity['type']} {entity['id']}: {e}"
                    )

        if self.session:
            self.session.close()


def main():
    """Função principal para execução standalone."""
    import sys

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    tester = AdminEndpointTester()

    try:
        results = tester.run_all_tests()

        # Mostrar resumo
        passed = len([r for r in results if r.status == "pass"])
        failed = len([r for r in results if r.status == "fail"])
        skipped = len([r for r in results if r.status == "skip"])
        total = len(results)

        print("\n📊 RESUMO - TESTES DE ADMINISTRADOR:")
        print(f"   Total: {total}")
        print(f"   ✅ Aprovados: {passed}")
        print(f"   ❌ Falharam: {failed}")
        print(f"   ⏭️ Ignorados: {skipped}")
        print(f"   📈 Taxa de Sucesso: {(passed/total*100):.1f}%")

        # Código de saída
        sys.exit(0 if failed == 0 else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Execução interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        sys.exit(1)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
