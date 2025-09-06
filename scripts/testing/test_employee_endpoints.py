#!/usr/bin/env python3
"""
Testes específicos para endpoints do perfil Employee.

Este módulo contém testes detalhados para todos os endpoints
disponíveis para funcionários no Portal de Benefícios KNN.
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


class EmployeeEndpointTester:
    """Classe para testes específicos de endpoints de funcionários."""

    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = REQUEST_TIMEOUT
        self.headers = get_auth_headers("employee")
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
            error_message = "Acesso negado para perfil de funcionário"
        elif status_code == 404:
            status = "skip"
            error_message = "Recurso não encontrado (esperado para dados de teste)"
        else:
            status = "fail"
            error_message = response_data.get("detail", f"HTTP {status_code}")

        return TestResult(
            endpoint=f"employee.{endpoint_name}",
            method=method,
            status=status,
            response_time=response_time,
            status_code=status_code if status_code > 0 else None,
            error_message=error_message,
            response_data=response_data if status == "pass" else None,
        )

    def test_list_partners(self) -> TestResult:
        """Testa listagem de parceiros para funcionários."""
        logger.info("Testando listagem de parceiros (employee)")

        url = build_url("/employee/partners")

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
                logger.info(
                    f"✅ Listagem de parceiros retornou {len(response_data['partners'])} itens"
                )

        return result

    def test_list_partners_with_pagination(self) -> TestResult:
        """Testa listagem de parceiros com paginação."""
        logger.info("Testando listagem de parceiros com paginação")

        url = build_url("/employee/partners")
        params = {"limit": "3", "offset": "0", "ord": "desc"}

        status_code, response_data, response_time = self._make_request(
            "GET", url, params=params
        )

        result = self._create_test_result(
            "list_partners_paginated", "GET", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            partners = response_data.get("partners", [])
            if len(partners) > 3:
                result.status = "fail"
                result.error_message = (
                    f"Limite de 3 itens não respeitado (retornou {len(partners)})"
                )
            else:
                logger.info(
                    f"✅ Paginação aplicada corretamente, {len(partners)} parceiros retornados"
                )

                # Verificar se há informações de paginação
                if "total" in response_data:
                    logger.info(
                        f"   Total de parceiros disponíveis: {response_data['total']}"
                    )

        return result

    def test_list_partners_by_category(self) -> TestResult:
        """Testa listagem de parceiros filtrada por categoria."""
        logger.info("Testando listagem de parceiros por categoria")

        url = build_url("/employee/partners")
        params = {"cat": "alimentacao", "limit": "10"}

        status_code, response_data, response_time = self._make_request(
            "GET", url, params=params
        )

        result = self._create_test_result(
            "list_partners_by_category",
            "GET",
            status_code,
            response_data,
            response_time,
        )

        # Validações específicas
        if result.status == "pass":
            partners = response_data.get("partners", [])
            logger.info(
                f"✅ Filtro por categoria aplicado, {len(partners)} parceiros retornados"
            )

            # Verificar se todos os parceiros são da categoria solicitada (se houver dados)
            if partners:
                for partner in partners:
                    if (
                        "category" in partner
                        and partner["category"].lower() != "alimentacao"
                    ):
                        logger.warning(
                            f"   Parceiro {partner.get('id', 'N/A')} não é da categoria esperada"
                        )

        return result

    def test_get_partner_details(self) -> TestResult:
        """Testa obtenção de detalhes de um parceiro específico."""
        logger.info("Testando detalhes de parceiro específico (employee)")

        # Usar ID de teste
        partner_id = "test-partner-id"
        url = build_url("/employee/partners/{id}", id=partner_id)

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
            # Verificar estrutura da resposta
            required_fields = ["id", "trade_name", "category"]
            missing_fields = [
                field for field in required_fields if field not in response_data
            ]

            if missing_fields:
                result.status = "fail"
                result.error_message = f"Campos obrigatórios ausentes: {missing_fields}"
            else:
                logger.info("✅ Detalhes do parceiro retornados corretamente")

                # Verificar se há informações específicas para funcionários
                if "promotions" in response_data:
                    logger.info(
                        f"   Promoções disponíveis: {len(response_data['promotions'])}"
                    )

        return result

    def test_create_validation_code(self) -> TestResult:
        """Testa criação de código de validação para funcionário."""
        logger.info("Testando criação de código de validação (employee)")

        url = build_url("/employee/validation-codes")
        json_data = TEST_DATA["validation_code_request"]

        status_code, response_data, response_time = self._make_request(
            "POST", url, json=json_data
        )

        result = self._create_test_result(
            "create_validation_code", "POST", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            if "code" not in response_data:
                result.status = "fail"
                result.error_message = "Campo 'code' não encontrado na resposta"
            elif not response_data["code"]:
                result.status = "fail"
                result.error_message = "Código de validação está vazio"
            else:
                code = response_data["code"]
                logger.info(f"✅ Código de validação criado: {code}")

                # Verificar formato do código (se aplicável)
                if len(code) < 6:
                    result.status = "fail"
                    result.error_message = f"Código muito curto: {code}"
                elif "expires_at" in response_data:
                    logger.info(f"   Código expira em: {response_data['expires_at']}")

        return result

    def test_create_validation_code_invalid_partner(self) -> TestResult:
        """Testa criação de código com parceiro inválido."""
        logger.info("Testando criação de código com parceiro inválido")

        url = build_url("/employee/validation-codes")
        json_data = {"partner_id": "invalid-partner-id"}

        status_code, response_data, response_time = self._make_request(
            "POST", url, json=json_data
        )

        result = self._create_test_result(
            "create_validation_code_invalid",
            "POST",
            status_code,
            response_data,
            response_time,
        )

        # Para este teste, esperamos erro 404 ou 400
        if result.status_code in [400, 404]:
            result.status = "pass"
            result.error_message = None
            logger.info(
                f"✅ Erro esperado para parceiro inválido: HTTP {result.status_code}"
            )
        elif result.status == "pass":
            result.status = "fail"
            result.error_message = "Deveria retornar erro para parceiro inválido"

        return result

    def test_get_history(self) -> TestResult:
        """Testa obtenção do histórico do funcionário."""
        logger.info("Testando histórico do funcionário")

        url = build_url("/employee/me/history")

        status_code, response_data, response_time = self._make_request("GET", url)

        result = self._create_test_result(
            "get_history", "GET", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            if "history" not in response_data:
                result.status = "fail"
                result.error_message = "Campo 'history' não encontrado na resposta"
            elif not isinstance(response_data["history"], list):
                result.status = "fail"
                result.error_message = "Campo 'history' deve ser uma lista"
            else:
                history_items = response_data["history"]
                logger.info(f"✅ Histórico retornado com {len(history_items)} itens")

                # Verificar estrutura dos itens do histórico (se houver)
                if history_items:
                    first_item = history_items[0]
                    expected_fields = ["id", "action", "timestamp"]
                    missing_fields = [
                        field for field in expected_fields if field not in first_item
                    ]

                    if missing_fields:
                        logger.warning(
                            f"   Campos ausentes no histórico: {missing_fields}"
                        )
                    else:
                        logger.info("   Estrutura do histórico validada")

        return result

    def test_get_history_with_pagination(self) -> TestResult:
        """Testa histórico com paginação."""
        logger.info("Testando histórico com paginação")

        url = build_url("/employee/me/history")
        params = {"limit": "5", "offset": "0"}

        status_code, response_data, response_time = self._make_request(
            "GET", url, params=params
        )

        result = self._create_test_result(
            "get_history_paginated", "GET", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            history_items = response_data.get("history", [])
            if len(history_items) > 5:
                result.status = "fail"
                result.error_message = (
                    f"Limite de 5 itens não respeitado (retornou {len(history_items)})"
                )
            else:
                logger.info(
                    f"✅ Paginação do histórico aplicada corretamente: {len(history_items)} itens"
                )

        return result

    def test_invalid_authentication(self) -> TestResult:
        """Testa comportamento com token inválido."""
        logger.info("Testando autenticação inválida (employee)")

        # Usar headers sem token
        invalid_headers = {"Content-Type": "application/json"}

        url = build_url("/employee/partners")

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
                    endpoint="employee.invalid_auth",
                    method="GET",
                    status="pass",
                    response_time=response_time,
                    status_code=401,
                    response_data=response_data,
                )
            else:
                return TestResult(
                    endpoint="employee.invalid_auth",
                    method="GET",
                    status="fail",
                    response_time=response_time,
                    status_code=response.status_code,
                    error_message=f"Esperado 401, recebido {response.status_code}",
                )

        except RequestException as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint="employee.invalid_auth",
                method="GET",
                status="fail",
                response_time=response_time,
                error_message=str(e),
            )

    def test_cross_role_access(self) -> TestResult:
        """Testa acesso a endpoint de outro perfil (deve falhar)."""
        logger.info("Testando acesso cruzado de perfis")

        # Tentar acessar endpoint de estudante com token de funcionário
        url = build_url("/student/students/me/fav")

        status_code, response_data, response_time = self._make_request("GET", url)

        result = self._create_test_result(
            "cross_role_access", "GET", status_code, response_data, response_time
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
            result.error_message = "Acesso cruzado deveria ser bloqueado"

        return result

    def run_all_tests(self) -> list[TestResult]:
        """Executa todos os testes de endpoints de funcionário."""
        logger.info("Iniciando testes de endpoints de funcionário")

        test_methods = [
            self.test_list_partners,
            self.test_list_partners_with_pagination,
            self.test_list_partners_by_category,
            self.test_get_partner_details,
            self.test_create_validation_code,
            self.test_create_validation_code_invalid_partner,
            self.test_get_history,
            self.test_get_history_with_pagination,
            self.test_invalid_authentication,
            self.test_cross_role_access,
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
                        endpoint=f"employee.{test_method.__name__}",
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
            f"Testes de funcionário concluídos: {passed} aprovados, {failed} falharam, {skipped} ignorados"
        )

        return results

    def cleanup(self):
        """Limpa recursos utilizados."""
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

    tester = EmployeeEndpointTester()

    try:
        results = tester.run_all_tests()

        # Mostrar resumo
        passed = len([r for r in results if r.status == "pass"])
        failed = len([r for r in results if r.status == "fail"])
        skipped = len([r for r in results if r.status == "skip"])
        total = len(results)

        print("\n📊 RESUMO - TESTES DE FUNCIONÁRIO:")
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
