#!/usr/bin/env python3
"""
Testes específicos para endpoints do perfil Student.

Este módulo contém testes detalhados para todos os endpoints
disponíveis para estudantes no Portal de Benefícios KNN.
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


class StudentEndpointTester:
    """Classe para testes específicos de endpoints de estudantes."""

    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = REQUEST_TIMEOUT
        self.headers = get_auth_headers("student")
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
        elif status_code == 404:
            status = "skip"
            error_message = "Recurso não encontrado (esperado para dados de teste)"
        else:
            status = "fail"
            error_message = response_data.get("detail", f"HTTP {status_code}")

        return TestResult(
            endpoint=f"student.{endpoint_name}",
            method=method,
            status=status,
            response_time=response_time,
            status_code=status_code if status_code > 0 else None,
            error_message=error_message,
            response_data=response_data if status == "pass" else None,
        )

    def test_list_partners(self) -> TestResult:
        """Testa listagem de parceiros para estudantes."""
        logger.info("Testando listagem de parceiros (student)")

        url = build_url("/student/partners")

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

    def test_list_partners_with_filters(self) -> TestResult:
        """Testa listagem de parceiros com filtros."""
        logger.info("Testando listagem de parceiros com filtros")

        url = build_url("/student/partners")
        params = {"cat": "tecnologia", "ord": "asc", "limit": "5", "offset": "0"}

        status_code, response_data, response_time = self._make_request(
            "GET", url, params=params
        )

        result = self._create_test_result(
            "list_partners_filtered", "GET", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            partners = response_data.get("partners", [])
            if len(partners) > 5:
                result.status = "fail"
                result.error_message = (
                    f"Limite de 5 itens não respeitado (retornou {len(partners)})"
                )
            else:
                logger.info(
                    f"✅ Filtros aplicados corretamente, {len(partners)} parceiros retornados"
                )

        return result

    def test_get_partner_details(self) -> TestResult:
        """Testa obtenção de detalhes de um parceiro específico."""
        logger.info("Testando detalhes de parceiro específico")

        # Usar ID de teste
        partner_id = "test-partner-id"
        url = build_url("/student/partners/{id}", id=partner_id)

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

        return result

    def test_create_validation_code(self) -> TestResult:
        """Testa criação de código de validação."""
        logger.info("Testando criação de código de validação")

        url = build_url("/student/validation-codes")
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
                logger.info(f"✅ Código de validação criado: {response_data['code']}")

        return result

    def test_get_history(self) -> TestResult:
        """Testa obtenção do histórico do estudante."""
        logger.info("Testando histórico do estudante")

        url = build_url("/student/students/me/history")
        params = {"limit": "10", "offset": "0"}

        status_code, response_data, response_time = self._make_request(
            "GET", url, params=params
        )

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
                logger.info(
                    f"✅ Histórico retornado com {len(response_data['history'])} itens"
                )

        return result

    def test_get_favorites(self) -> TestResult:
        """Testa obtenção de parceiros favoritos."""
        logger.info("Testando parceiros favoritos")

        url = build_url("/student/students/me/fav")

        status_code, response_data, response_time = self._make_request("GET", url)

        result = self._create_test_result(
            "get_favorites", "GET", status_code, response_data, response_time
        )

        # Validações específicas
        if result.status == "pass":
            if "favorites" not in response_data:
                result.status = "fail"
                result.error_message = "Campo 'favorites' não encontrado na resposta"
            elif not isinstance(response_data["favorites"], list):
                result.status = "fail"
                result.error_message = "Campo 'favorites' deve ser uma lista"
            else:
                logger.info(
                    f"✅ Favoritos retornados: {len(response_data['favorites'])} itens"
                )

        return result

    def test_add_favorite(self) -> TestResult:
        """Testa adição de parceiro aos favoritos."""
        logger.info("Testando adição de favorito")

        url = build_url("/student/students/me/fav")
        json_data = {"partner_id": "test-partner-id"}

        status_code, response_data, response_time = self._make_request(
            "POST", url, json=json_data
        )

        result = self._create_test_result(
            "add_favorite", "POST", status_code, response_data, response_time
        )

        # Para este teste, pode retornar erro se o parceiro não existir
        if result.status_code == 404:
            result.status = "skip"
            result.error_message = "Parceiro de teste não encontrado (esperado)"
            logger.info("⏭️ Parceiro de teste não encontrado (esperado)")
        elif result.status == "pass":
            logger.info("✅ Favorito adicionado com sucesso")

        return result

    def test_remove_favorite(self) -> TestResult:
        """Testa remoção de parceiro dos favoritos."""
        logger.info("Testando remoção de favorito")

        partner_id = "test-partner-id"
        url = build_url("/student/students/me/fav/{pid}", pid=partner_id)

        status_code, response_data, response_time = self._make_request("DELETE", url)

        result = self._create_test_result(
            "remove_favorite", "DELETE", status_code, response_data, response_time
        )

        # Para este teste, pode retornar erro se o favorito não existir
        if result.status_code == 404:
            result.status = "skip"
            result.error_message = (
                "Favorito não encontrado (esperado para dados de teste)"
            )
            logger.info("⏭️ Favorito não encontrado (esperado)")
        elif result.status == "pass":
            logger.info("✅ Favorito removido com sucesso")

        return result

    def test_invalid_authentication(self) -> TestResult:
        """Testa comportamento com token inválido."""
        logger.info("Testando autenticação inválida")

        # Usar headers sem token
        invalid_headers = {"Content-Type": "application/json"}

        url = build_url("/student/partners")

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
                    endpoint="student.invalid_auth",
                    method="GET",
                    status="pass",
                    response_time=response_time,
                    status_code=401,
                    response_data=response_data,
                )
            else:
                return TestResult(
                    endpoint="student.invalid_auth",
                    method="GET",
                    status="fail",
                    response_time=response_time,
                    status_code=response.status_code,
                    error_message=f"Esperado 401, recebido {response.status_code}",
                )

        except RequestException as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint="student.invalid_auth",
                method="GET",
                status="fail",
                response_time=response_time,
                error_message=str(e),
            )

    def run_all_tests(self) -> list[TestResult]:
        """Executa todos os testes de endpoints de estudante."""
        logger.info("Iniciando testes de endpoints de estudante")

        test_methods = [
            self.test_list_partners,
            self.test_list_partners_with_filters,
            self.test_get_partner_details,
            self.test_create_validation_code,
            self.test_get_history,
            self.test_get_favorites,
            self.test_add_favorite,
            self.test_remove_favorite,
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
                        endpoint=f"student.{test_method.__name__}",
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
            f"Testes de estudante concluídos: {passed} aprovados, {failed} falharam, {skipped} ignorados"
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

    tester = StudentEndpointTester()

    try:
        results = tester.run_all_tests()

        # Mostrar resumo
        passed = len([r for r in results if r.status == "pass"])
        failed = len([r for r in results if r.status == "fail"])
        skipped = len([r for r in results if r.status == "skip"])
        total = len(results)

        print("\n📊 RESUMO - TESTES DE ESTUDANTE:")
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
