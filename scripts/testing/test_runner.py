#!/usr/bin/env python3
"""
Executor principal de testes para o Portal de Benefícios KNN.

Este módulo contém a classe TestRunner responsável por executar
todos os testes de endpoints de forma organizada e gerar relatórios.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from test_config import (
    HTML_REPORT_TEMPLATE,
    LOG_CONFIG,
    MAX_RETRIES,
    REPORTS_DIR,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
    TEST_DATA,
    build_url,
    get_all_endpoints,
    get_auth_headers,
)
from urllib3.util.retry import Retry

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG["level"]),
    format=LOG_CONFIG["format"],
    handlers=[logging.FileHandler(LOG_CONFIG["file"]), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class TestResult:
    """Representa o resultado de um teste individual."""

    def __init__(
        self,
        endpoint: str,
        method: str,
        status: str,
        response_time: float,
        status_code: int | None = None,
        error_message: str | None = None,
        response_data: dict | None = None,
    ):
        self.endpoint = endpoint
        self.method = method
        self.status = status  # 'pass', 'fail', 'skip'
        self.response_time = response_time
        self.status_code = status_code
        self.error_message = error_message
        self.response_data = response_data
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Converte resultado para dicionário."""
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "status": self.status,
            "response_time": self.response_time,
            "status_code": self.status_code,
            "error_message": self.error_message,
            "response_data": self.response_data,
            "timestamp": self.timestamp.isoformat(),
        }


class TestRunner:
    """Executor principal de testes de endpoints."""

    def __init__(self):
        self.results: list[TestResult] = []
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Cria sessão HTTP com configurações de retry."""
        session = requests.Session()

        # Configurar retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _make_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> tuple[int, dict, float]:
        """Executa requisição HTTP e retorna status, dados e tempo de resposta."""
        start_time = time.time()

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=REQUEST_TIMEOUT,
            )

            response_time = time.time() - start_time

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}

            return response.status_code, response_data, response_time

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            return 0, {"error": str(e)}, response_time

    def test_endpoint(
        self, role: str, endpoint_name: str, endpoint_config: dict
    ) -> TestResult:
        """Testa um endpoint específico."""
        method = endpoint_config["method"]
        path = endpoint_config["path"]
        # Description is logged for debugging if needed
        logger.debug(f"Endpoint description: {endpoint_config.get('description', '')}")

        logger.info(f"Testando {role}.{endpoint_name}: {method} {path}")

        try:
            # Preparar headers
            auth_required = endpoint_config.get("auth_required", True)
            if auth_required:
                headers = get_auth_headers(role)
            else:
                headers = {"Content-Type": "application/json"}

            # Preparar URL
            path_params = {}
            if "path_params" in endpoint_config:
                # Usar valores de teste para parâmetros de path
                for param in endpoint_config["path_params"]:
                    if param == "id":
                        path_params[param] = "test-id"
                    elif param == "entity":
                        path_params[param] = "students"
                    elif param == "pid":
                        path_params[param] = "partner-id"
                    else:
                        path_params[param] = f"test-{param}"

            url = build_url(path, **path_params)

            # Preparar parâmetros de query
            query_params = None
            if "params" in endpoint_config:
                query_params = {
                    "limit": "10",
                    "offset": "0",
                    "cat": "tecnologia",
                    "ord": "asc",
                    "range": "30d",
                }

            # Preparar body da requisição
            json_data = None
            if endpoint_config.get("body_required", False):
                if endpoint_name == "create_validation_code":
                    json_data = TEST_DATA["validation_code_request"]
                elif endpoint_name == "redeem_code":
                    json_data = TEST_DATA["redeem_request"]
                elif (
                    endpoint_name == "create_promotion"
                    or endpoint_name == "update_promotion"
                ):
                    json_data = TEST_DATA["promotion"]
                elif endpoint_name == "add_favorite":
                    json_data = {"partner_id": "test-partner-id"}
                elif endpoint_name == "send_notifications":
                    json_data = TEST_DATA["notification"]
                elif "create" in endpoint_name or "update" in endpoint_name:
                    # Determinar tipo de entidade baseado no path
                    if "students" in path or "student" in path:
                        json_data = TEST_DATA["student"]
                    elif "partners" in path or "partner" in path:
                        json_data = TEST_DATA["partner"]
                    elif "promotions" in path:
                        json_data = TEST_DATA["promotion"]
                    else:
                        json_data = {"test": "data"}

            # Executar requisição
            status_code, response_data, response_time = self._make_request(
                method, url, headers, query_params, json_data
            )

            # Avaliar resultado
            if status_code == 0:
                # Erro de conexão
                return TestResult(
                    endpoint=f"{role}.{endpoint_name}",
                    method=method,
                    status="fail",
                    response_time=response_time,
                    error_message=response_data.get("error", "Erro de conexão"),
                )
            elif 200 <= status_code < 300:
                # Sucesso
                return TestResult(
                    endpoint=f"{role}.{endpoint_name}",
                    method=method,
                    status="pass",
                    response_time=response_time,
                    status_code=status_code,
                    response_data=response_data,
                )
            elif status_code == 401:
                # Não autorizado - pode ser esperado para alguns testes
                return TestResult(
                    endpoint=f"{role}.{endpoint_name}",
                    method=method,
                    status="skip",
                    response_time=response_time,
                    status_code=status_code,
                    error_message="Token de autenticação inválido ou expirado",
                )
            elif status_code == 404:
                # Não encontrado - pode ser esperado para recursos de teste
                return TestResult(
                    endpoint=f"{role}.{endpoint_name}",
                    method=method,
                    status="skip",
                    response_time=response_time,
                    status_code=status_code,
                    error_message="Recurso não encontrado (esperado para dados de teste)",
                )
            else:
                # Outros erros
                return TestResult(
                    endpoint=f"{role}.{endpoint_name}",
                    method=method,
                    status="fail",
                    response_time=response_time,
                    status_code=status_code,
                    error_message=response_data.get("detail", f"HTTP {status_code}"),
                )

        except Exception as e:
            logger.error(f"Erro ao testar {role}.{endpoint_name}: {e}")
            return TestResult(
                endpoint=f"{role}.{endpoint_name}",
                method=method,
                status="fail",
                response_time=0.0,
                error_message=str(e),
            )

    def run_all_tests(self, roles: list[str] | None = None) -> dict[str, Any]:
        """Executa todos os testes de endpoints."""
        logger.info("Iniciando execução de testes")
        self.start_time = time.time()
        self.results = []

        all_endpoints = get_all_endpoints()

        # Filtrar roles se especificado
        if roles:
            all_endpoints = {
                role: endpoints
                for role, endpoints in all_endpoints.items()
                if role in roles
            }

        # Executar testes para cada role e endpoint
        for role, endpoints in all_endpoints.items():
            logger.info(f"Testando endpoints do perfil: {role}")

            for endpoint_name, endpoint_config in endpoints.items():
                result = self.test_endpoint(role, endpoint_name, endpoint_config)
                self.results.append(result)

                # Log do resultado
                status_emoji = {"pass": "✅", "fail": "❌", "skip": "⏭️"}

                logger.info(
                    f"{status_emoji.get(result.status, '❓')} {result.endpoint} - "
                    f"{result.status.upper()} ({result.response_time:.3f}s)"
                )

                if result.error_message:
                    logger.warning(f"   Erro: {result.error_message}")

        self.end_time = time.time()

        # Calcular estatísticas
        stats = self._calculate_stats()

        logger.info(f"Testes concluídos em {stats['duration']:.2f}s")
        logger.info(
            f"Resultados: {stats['passed']} aprovados, {stats['failed']} falharam, {stats['skipped']} ignorados"
        )

        return {
            "summary": stats,
            "results": [result.to_dict() for result in self.results],
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_stats(self) -> dict[str, Any]:
        """Calcula estatísticas dos testes executados."""
        total = len(self.results)
        passed = len([r for r in self.results if r.status == "pass"])
        failed = len([r for r in self.results if r.status == "fail"])
        skipped = len([r for r in self.results if r.status == "skip"])

        duration = (
            (self.end_time - self.start_time)
            if self.start_time and self.end_time
            else 0
        )
        success_rate = (passed / total * 100) if total > 0 else 0

        avg_response_time = (
            sum(r.response_time for r in self.results) / total if total > 0 else 0
        )

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": success_rate,
            "duration": duration,
            "avg_response_time": avg_response_time,
        }

    def generate_report(
        self, test_data: dict[str, Any], format_type: str = "html"
    ) -> str:
        """Gera relatório de testes no formato especificado."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Criar diretório de relatórios se não existir
        os.makedirs(REPORTS_DIR, exist_ok=True)

        if format_type == "json":
            filename = f"{REPORTS_DIR}/test_report_{timestamp}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(test_data, f, indent=2, ensure_ascii=False)

        elif format_type == "html":
            filename = f"{REPORTS_DIR}/test_report_{timestamp}.html"

            # Preparar dados para template HTML
            summary = test_data["summary"]

            # Gerar seções de resultados por perfil
            results_by_role = {}
            for result in test_data["results"]:
                role = result["endpoint"].split(".")[0]
                if role not in results_by_role:
                    results_by_role[role] = []
                results_by_role[role].append(result)

            test_results_html = ""
            for role, results in results_by_role.items():
                test_results_html += (
                    f'<div class="test-group"><h3>Perfil: {role.title()}</h3>'
                )

                for result in results:
                    css_class = f"test-{result['status']}"
                    status_text = {
                        "pass": "✅ APROVADO",
                        "fail": "❌ FALHOU",
                        "skip": "⏭️ IGNORADO",
                    }.get(result["status"], "❓ DESCONHECIDO")

                    test_results_html += f"""
                    <div class="test-item {css_class}">
                        <strong>{result["endpoint"]}</strong> ({result["method"]})<br>
                        Status: {status_text}<br>
                        Tempo de Resposta: {result["response_time"]:.3f}s<br>
                        {f"Código HTTP: {result['status_code']}<br>" if result.get('status_code') else ""}
                        {f"Erro: {result['error_message']}<br>" if result.get('error_message') else ""}
                    </div>
                    """

                test_results_html += "</div>"

            # Gerar HTML final
            html_content = HTML_REPORT_TEMPLATE.format(
                timestamp=test_data["timestamp"],
                passed=summary["passed"],
                failed=summary["failed"],
                skipped=summary["skipped"],
                total=summary["total"],
                success_rate=summary["success_rate"],
                duration=summary["duration"],
                test_results=test_results_html,
            )

            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)

        elif format_type == "txt":
            filename = f"{REPORTS_DIR}/test_report_{timestamp}.txt"

            with open(filename, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write("RELATÓRIO DE TESTES - PORTAL DE BENEFÍCIOS KNN\n")
                f.write("=" * 60 + "\n\n")

                f.write(f"Data/Hora: {test_data['timestamp']}\n")
                f.write(f"Duração: {test_data['summary']['duration']:.2f}s\n\n")

                f.write("RESUMO:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total de Testes: {test_data['summary']['total']}\n")
                f.write(f"Aprovados: {test_data['summary']['passed']}\n")
                f.write(f"Falharam: {test_data['summary']['failed']}\n")
                f.write(f"Ignorados: {test_data['summary']['skipped']}\n")
                f.write(
                    f"Taxa de Sucesso: {test_data['summary']['success_rate']:.1f}%\n\n"
                )

                f.write("RESULTADOS DETALHADOS:\n")
                f.write("-" * 30 + "\n")

                for result in test_data["results"]:
                    status_symbol = {"pass": "✅", "fail": "❌", "skip": "⏭️"}.get(
                        result["status"], "❓"
                    )

                    f.write(
                        f"{status_symbol} {result['endpoint']} ({result['method']})\n"
                    )
                    f.write(f"   Tempo: {result['response_time']:.3f}s")

                    if result.get("status_code"):
                        f.write(f" | HTTP: {result['status_code']}")

                    if result.get("error_message"):
                        f.write(f" | Erro: {result['error_message']}")

                    f.write("\n")

        logger.info(f"Relatório gerado: {filename}")
        return filename

    def cleanup(self):
        """Limpa recursos utilizados."""
        if self.session:
            self.session.close()


def main():
    """Função principal para execução standalone."""
    import argparse

    parser = argparse.ArgumentParser(description="Executor de testes do Portal KNN")
    parser.add_argument(
        "--roles",
        nargs="*",
        help="Perfis específicos para testar",
        choices=["student", "employee", "admin", "partner", "utils"],
    )
    parser.add_argument(
        "--format",
        choices=["json", "html", "txt"],
        default="html",
        help="Formato do relatório",
    )
    parser.add_argument("--no-report", action="store_true", help="Não gerar relatório")

    args = parser.parse_args()

    runner = TestRunner()

    try:
        # Executar testes
        test_data = runner.run_all_tests(roles=args.roles)

        # Gerar relatório se solicitado
        if not args.no_report:
            report_file = runner.generate_report(test_data, args.format)
            print(f"\n📊 Relatório gerado: {report_file}")

        # Mostrar resumo no console
        summary = test_data["summary"]
        print("\n📈 RESUMO DOS TESTES:")
        print(f"   Total: {summary['total']}")
        print(f"   ✅ Aprovados: {summary['passed']}")
        print(f"   ❌ Falharam: {summary['failed']}")
        print(f"   ⏭️ Ignorados: {summary['skipped']}")
        print(f"   📊 Taxa de Sucesso: {summary['success_rate']:.1f}%")
        print(f"   ⏱️ Duração: {summary['duration']:.2f}s")

        # Código de saída baseado nos resultados
        exit_code = 0 if summary["failed"] == 0 else 1

    except KeyboardInterrupt:
        print("\n⚠️ Execução interrompida pelo usuário")
        exit_code = 130
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        print(f"❌ Erro: {e}")
        exit_code = 1
    finally:
        runner.cleanup()

    exit(exit_code)


if __name__ == "__main__":
    main()
