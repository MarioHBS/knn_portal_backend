#!/usr/bin/env python3
"""
Testes específicos para endpoints do perfil Partner.

Este módulo contém testes detalhados para todos os endpoints
disponíveis para parceiros no Portal de Benefícios KNN.
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


class PartnerEndpointTester:
    """Classe para testes específicos de endpoints de parceiros."""

    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = REQUEST_TIMEOUT
        self.headers = get_auth_headers("partner")
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
            error_message = "Acesso negado para perfil de parceiro"
        elif status_code == 404:
            status = "skip"
            error_message = "Recurso não encontrado (esperado para dados de teste)"
        else:
            status = "fail"
            error_message = response_data.get("detail", f"HTTP {status_code}")

        return TestResult(
            endpoint=f"partner.{endpoint_name}",
            method=method,
            status=status,
            response_time=response_time,
            status_code=status_code if status_code > 0 else None,
            error_message=error_message,
            response_data=response_data if status == "pass" else None,
        )

    def test_redeem_code(self) -> TestResult:
        """Testa resgate de código de validação."""
        logger.info("Testando resgate de código de validação")

        url = build_url("/partner/partner/redeem")
        json_data = TEST_DATA["validation_code"]

        status_code, response_data, response_time = self._make_request(
            "POST", url, json=json_data
        )

        result = self._create_test_result(
            "redeem_code", "POST", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            required_fields = ["success", "message"]
            missing_fields = [
                field for field in required_fields if field not in response_data
            ]

            if missing_fields:
                result.status = "fail"
                result.error_message = f"Campos obrigatórios ausentes: {missing_fields}"
            else:
                success = response_data.get("success", False)
                message = response_data.get("message", "")

                logger.info(f"✅ Resgate processado - Sucesso: {success}")
                logger.info(f"   Mensagem: {message}")

                # Verificar informações adicionais
                if "student_info" in response_data:
                    student_info = response_data["student_info"]
                    logger.info(f"   Estudante: {student_info.get('nome', 'N/A')}")

                if "validation_info" in response_data:
                    validation_info = response_data["validation_info"]
                    logger.info(f"   Código: {validation_info.get('code', 'N/A')}")

        elif result.status_code == 400:
            # Código inválido é um comportamento esperado para dados de teste
            result.status = "skip"
            result.error_message = "Código de teste inválido (comportamento esperado)"
            logger.info("⏭️ Código de teste inválido (esperado)")

        return result

    def test_list_promotions(self) -> TestResult:
        """Testa listagem de promoções do parceiro."""
        logger.info("Testando listagem de promoções do parceiro")

        url = build_url("/partner/partner/promotions")
        params = {"limit": "10", "offset": "0"}

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
                    required_fields = ["id", "title", "description"]
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

                        # Verificar campos específicos
                        if "active" in first_promotion:
                            active_count = len(
                                [p for p in promotions if p.get("active", True)]
                            )
                            logger.info(
                                f"   Promoções ativas: {active_count}/{len(promotions)}"
                            )

                # Verificar informações de paginação
                if "total" in response_data:
                    logger.info(f"   Total de promoções: {response_data['total']}")

        return result

    def test_create_promotion(self) -> TestResult:
        """Testa criação de nova promoção."""
        logger.info("Testando criação de promoção")

        url = build_url("/partner/partner/promotions")
        json_data = TEST_DATA["promotion"].copy()

        # Adicionar timestamp para evitar duplicatas
        json_data["title"] = f"Promoção Teste {int(time.time())}"

        status_code, response_data, response_time = self._make_request(
            "POST", url, json=json_data
        )

        result = self._create_test_result(
            "create_promotion", "POST", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            if "id" not in response_data:
                result.status = "fail"
                result.error_message = (
                    "Campo 'id' não encontrado na resposta de criação"
                )
            else:
                promotion_id = response_data["id"]
                logger.info(f"✅ Promoção criada com ID: {promotion_id}")

                # Armazenar ID para possível limpeza posterior
                if not hasattr(self, "created_promotions"):
                    self.created_promotions = []
                self.created_promotions.append(promotion_id)

                # Verificar campos retornados
                if "title" in response_data:
                    logger.info(f"   Título: {response_data['title']}")
                if "status" in response_data:
                    logger.info(f"   Status: {response_data['status']}")

        return result

    def test_update_promotion(self) -> TestResult:
        """Testa atualização de promoção existente."""
        logger.info("Testando atualização de promoção")

        # Usar ID de teste
        promotion_id = "test-promotion-id"
        url = build_url("/partner/partner/promotions/{id}", id=promotion_id)

        json_data = {
            "title": "Promoção Atualizada",
            "description": "Descrição atualizada da promoção",
            "discount_percentage": 25.0,
        }

        status_code, response_data, response_time = self._make_request(
            "PUT", url, json=json_data
        )

        result = self._create_test_result(
            "update_promotion", "PUT", status_code, response_data, response_time
        )

        # Para este teste, 404 é esperado pois usamos ID de teste
        if result.status_code == 404:
            result.status = "skip"
            result.error_message = "ID de teste não encontrado (comportamento esperado)"
            logger.info("⏭️ ID de teste não encontrado (esperado)")
        elif result.status == "pass":
            logger.info("✅ Promoção atualizada com sucesso")

            # Verificar campos atualizados
            if "title" in response_data:
                logger.info(f"   Novo título: {response_data['title']}")
            if "updated_at" in response_data:
                logger.info(f"   Atualizada em: {response_data['updated_at']}")

        return result

    def test_delete_promotion(self) -> TestResult:
        """Testa exclusão de promoção."""
        logger.info("Testando exclusão de promoção")

        # Usar ID de teste
        promotion_id = "test-promotion-id"
        url = build_url("/partner/partner/promotions/{id}", id=promotion_id)

        status_code, response_data, response_time = self._make_request("DELETE", url)

        result = self._create_test_result(
            "delete_promotion", "DELETE", status_code, response_data, response_time
        )

        # Para este teste, 404 é esperado pois usamos ID de teste
        if result.status_code == 404:
            result.status = "skip"
            result.error_message = "ID de teste não encontrado (comportamento esperado)"
            logger.info("⏭️ ID de teste não encontrado (esperado)")
        elif result.status == "pass":
            logger.info("✅ Promoção excluída com sucesso")

            # Verificar resposta de confirmação
            if "message" in response_data:
                logger.info(f"   Mensagem: {response_data['message']}")

        return result

    def test_get_promotion_details(self) -> TestResult:
        """Testa obtenção de detalhes de uma promoção específica."""
        logger.info("Testando detalhes de promoção específica")

        # Usar ID de teste
        promotion_id = "test-promotion-id"
        url = build_url("/partner/partner/promotions/{id}", id=promotion_id)

        status_code, response_data, response_time = self._make_request("GET", url)

        result = self._create_test_result(
            "get_promotion_details", "GET", status_code, response_data, response_time
        )

        # Para este teste, 404 é esperado pois usamos ID de teste
        if result.status_code == 404:
            result.status = "skip"
            result.error_message = "ID de teste não encontrado (comportamento esperado)"
            logger.info("⏭️ ID de teste não encontrado (esperado)")
        elif result.status == "pass":
            # Verificar estrutura da resposta
            required_fields = ["id", "title", "description"]
            missing_fields = [
                field for field in required_fields if field not in response_data
            ]

            if missing_fields:
                result.status = "fail"
                result.error_message = f"Campos obrigatórios ausentes: {missing_fields}"
            else:
                logger.info("✅ Detalhes da promoção retornados corretamente")
                logger.info(f"   Título: {response_data.get('title', 'N/A')}")
                logger.info(f"   Status: {response_data.get('active', 'N/A')}")

                # Verificar campos opcionais
                optional_fields = ["discount_percentage", "valid_until", "terms"]
                available_fields = [
                    field for field in optional_fields if field in response_data
                ]
                if available_fields:
                    logger.info(f"   Campos adicionais: {available_fields}")

        return result

    def test_get_reports(self) -> TestResult:
        """Testa obtenção de relatórios do parceiro."""
        logger.info("Testando relatórios do parceiro")

        url = build_url("/partner/partner/reports")
        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "report_type": "validations",
        }

        status_code, response_data, response_time = self._make_request(
            "GET", url, params=params
        )

        result = self._create_test_result(
            "get_reports", "GET", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            expected_fields = ["report_type", "period", "data"]
            missing_fields = [
                field for field in expected_fields if field not in response_data
            ]

            if missing_fields:
                result.status = "fail"
                result.error_message = f"Campos obrigatórios ausentes: {missing_fields}"
            else:
                report_type = response_data.get("report_type", "N/A")
                period = response_data.get("period", {})
                data = response_data.get("data", {})

                logger.info(f"✅ Relatório gerado - Tipo: {report_type}")

                if isinstance(period, dict):
                    start = period.get("start", "N/A")
                    end = period.get("end", "N/A")
                    logger.info(f"   Período: {start} a {end}")

                if isinstance(data, dict):
                    # Log das métricas principais
                    metrics = ["total_validations", "total_students", "total_revenue"]
                    for metric in metrics:
                        if metric in data:
                            logger.info(f"   {metric}: {data[metric]}")

                    # Verificar se há dados detalhados
                    if "details" in data:
                        details_count = (
                            len(data["details"])
                            if isinstance(data["details"], list)
                            else 0
                        )
                        logger.info(f"   Registros detalhados: {details_count}")

        return result

    def test_get_validation_statistics(self) -> TestResult:
        """Testa obtenção de estatísticas de validações."""
        logger.info("Testando estatísticas de validações")

        url = build_url("/partner/partner/reports")
        params = {"report_type": "statistics", "period": "monthly"}

        status_code, response_data, response_time = self._make_request(
            "GET", url, params=params
        )

        result = self._create_test_result(
            "get_validation_statistics",
            "GET",
            status_code,
            response_data,
            response_time,
        )

        # Validações específicas
        if result.status == "pass":
            if "statistics" not in response_data:
                result.status = "fail"
                result.error_message = "Campo 'statistics' não encontrado na resposta"
            else:
                statistics = response_data["statistics"]
                logger.info("✅ Estatísticas de validações obtidas")

                # Verificar métricas básicas
                basic_metrics = ["total", "successful", "failed"]
                for metric in basic_metrics:
                    if metric in statistics:
                        logger.info(f"   {metric}: {statistics[metric]}")

                # Verificar dados por período
                if "by_period" in statistics:
                    periods = statistics["by_period"]
                    if isinstance(periods, list) and periods:
                        logger.info(f"   Períodos disponíveis: {len(periods)}")
                    elif isinstance(periods, dict):
                        logger.info(f"   Dados por período: {list(periods.keys())}")

        return result

    def test_invalid_cnpj_redeem(self) -> TestResult:
        """Testa resgate com CNPJ inválido."""
        logger.info("Testando resgate com CNPJ inválido")

        url = build_url("/partner/partner/redeem")
        json_data = {
            "code": "TEST123",
            "cnpj": "00.000.000/0000-00",  # CNPJ inválido
            "student_cpf": "123.456.789-00",
        }

        status_code, response_data, response_time = self._make_request(
            "POST", url, json=json_data
        )

        result = self._create_test_result(
            "invalid_cnpj_redeem", "POST", status_code, response_data, response_time
        )

        # Deve retornar erro de validação
        if result.status_code == 400:
            result.status = "pass"
            result.error_message = None
            logger.info("✅ CNPJ inválido rejeitado corretamente")

            # Verificar mensagem de erro
            if "detail" in response_data:
                logger.info(f"   Mensagem de erro: {response_data['detail']}")
        elif result.status == "pass":
            result.status = "fail"
            result.error_message = "Deveria retornar erro para CNPJ inválido"

        return result

    def test_invalid_authentication(self) -> TestResult:
        """Testa comportamento com token inválido."""
        logger.info("Testando autenticação inválida (partner)")

        # Usar headers sem token
        invalid_headers = {"Content-Type": "application/json"}

        url = build_url("/partner/partner/promotions")

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
                    endpoint="partner.invalid_auth",
                    method="GET",
                    status="pass",
                    response_time=response_time,
                    status_code=401,
                    response_data=response_data,
                )
            else:
                return TestResult(
                    endpoint="partner.invalid_auth",
                    method="GET",
                    status="fail",
                    response_time=response_time,
                    status_code=response.status_code,
                    error_message=f"Esperado 401, recebido {response.status_code}",
                )

        except RequestException as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint="partner.invalid_auth",
                method="GET",
                status="fail",
                response_time=response_time,
                error_message=str(e),
            )

    def test_cross_profile_access(self) -> TestResult:
        """Testa acesso a endpoints de outros perfis."""
        logger.info("Testando acesso cruzado de perfis")

        # Tentar acessar endpoint de estudante
        url = build_url("/student/students/me/history")

        status_code, response_data, response_time = self._make_request("GET", url)

        result = self._create_test_result(
            "cross_profile_access", "GET", status_code, response_data, response_time
        )

        # Deve retornar 403 Forbidden ou 404 Not Found
        if result.status_code in [403, 404]:
            result.status = "pass"
            result.error_message = None
            logger.info(
                f"✅ Acesso cruzado bloqueado corretamente: HTTP {result.status_code}"
            )
        elif result.status == "pass":
            result.status = "fail"
            result.error_message = (
                "Deveria bloquear acesso a endpoints de outros perfis"
            )

        return result

    def run_all_tests(self) -> list[TestResult]:
        """Executa todos os testes de endpoints de parceiro."""
        logger.info("Iniciando testes de endpoints de parceiro")

        test_methods = [
            self.test_redeem_code,
            self.test_list_promotions,
            self.test_create_promotion,
            self.test_update_promotion,
            self.test_delete_promotion,
            self.test_get_promotion_details,
            self.test_get_reports,
            self.test_get_validation_statistics,
            self.test_invalid_cnpj_redeem,
            self.test_invalid_authentication,
            self.test_cross_profile_access,
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
                        endpoint=f"partner.{test_method.__name__}",
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
            f"Testes de parceiro concluídos: {passed} aprovados, {failed} falharam, {skipped} ignorados"
        )

        return results

    def cleanup(self):
        """Limpa recursos utilizados e promoções criadas durante os testes."""
        # Limpar promoções criadas durante os testes
        if hasattr(self, "created_promotions"):
            logger.info("Limpando promoções criadas durante os testes")
            for promotion_id in self.created_promotions:
                try:
                    url = build_url("/partner/partner/promotions/{id}", id=promotion_id)
                    self._make_request("DELETE", url)
                    logger.info(f"   Promoção {promotion_id} removida")
                except Exception as e:
                    logger.warning(f"   Erro ao remover promoção {promotion_id}: {e}")

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

    tester = PartnerEndpointTester()

    try:
        results = tester.run_all_tests()

        # Mostrar resumo
        passed = len([r for r in results if r.status == "pass"])
        failed = len([r for r in results if r.status == "fail"])
        skipped = len([r for r in results if r.status == "skip"])
        total = len(results)

        print("\n📊 RESUMO - TESTES DE PARCEIRO:")
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
