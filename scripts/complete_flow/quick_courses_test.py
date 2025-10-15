#!/usr/bin/env python3
"""
Teste Rápido de Endpoints de Cursos - Portal KNN

Este script permite testar o endpoint de cursos.

Uso:
    python quick_courses_test.py --all                    # Testa todos os endpoints
    python quick_courses_test.py --endpoint courses_english # Testa endpoint específico
    python quick_courses_test.py --list                   # Lista endpoints disponíveis

Autor: Sistema de Testes KNN
Data: 2025-10-14
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any

import requests

# Adicionar o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from scripts.complete_flow.base_auth_test import (  # noqa: E402
    BACKEND_BASE_URL,
)

# Diretório para relatórios
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

# Mapeamento de endpoints disponíveis
ENDPOINTS = {
    "courses_all": {
        "url": "/courses/",
        "method": "GET",
        "description": "Lista de todos os cursos",
        "category": "courses",
    },
    "courses_english": {
        "url": "/courses/",
        "method": "GET",
        "description": "Lista de cursos de inglês",
        "category": "courses",
        "params": {"idiom": "english"},
    },
    "courses_spanish": {
        "url": "/courses/",
        "method": "GET",
        "description": "Lista de cursos de espanhol",
        "category": "courses",
        "params": {"idiom": "spanish"},
    },
}


class QuickCoursesTester:
    """Classe para testes rápidos de endpoints de cursos."""

    def __init__(self):
        """Inicializa o testador com configurações básicas."""
        self.session = requests.Session()
        self.results = []

    def print_colored(self, message: str, color: str = "white") -> None:
        """
        Imprime mensagem colorida no terminal.
        """
        colors = {
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "white": "\033[0m",
            "cyan": "\033[96m",
            "magenta": "\033[95m",
        }

        color_code = colors.get(color, colors["white"])
        reset_code = "\033[0m"
        print(f"{color_code}{message}{reset_code}")

    def print_header(self, title: str) -> None:
        """Imprime cabeçalho formatado."""
        self.print_colored("=" * 60, "cyan")
        self.print_colored(f" {title} ", "cyan")
        self.print_colored("=" * 60, "cyan")

    def test_endpoint(self, endpoint_key: str) -> dict[str, Any]:
        """
        Testa um endpoint específico.
        """
        if endpoint_key not in ENDPOINTS:
            return {
                "endpoint_key": endpoint_key,
                "success": False,
                "error": "Endpoint não encontrado",
                "timestamp": datetime.now().isoformat(),
            }

        result = self._execute_endpoint_request(endpoint_key)
        return result

    def _execute_endpoint_request(self, endpoint_key: str) -> dict[str, Any]:
        """
        Executa a requisição para um endpoint específico.
        """
        endpoint_config = ENDPOINTS[endpoint_key]
        url = f"{BACKEND_BASE_URL}{endpoint_config['url']}"
        method = endpoint_config["method"]
        params = endpoint_config.get("params")

        headers = {"Content-Type": "application/json"}

        self.print_colored(f"🔍 Testando: {endpoint_config['description']}", "blue")
        self.print_colored(f"   {method} {url}", "white")

        if params:
            self.print_colored(f"   🔧 Parâmetros: {params}", "magenta")

        try:
            response = self.session.request(
                method, url, headers=headers, params=params, timeout=30
            )

            result = {
                "endpoint_key": endpoint_key,
                "endpoint_url": endpoint_config["url"],
                "method": method,
                "description": endpoint_config["description"],
                "status_code": response.status_code,
                "success": response.status_code in [200, 201],
                "timestamp": datetime.now().isoformat(),
            }

            if response.status_code in [200, 201]:
                self.print_colored(f"   ✅ Sucesso: {response.status_code}", "green")
                try:
                    response_data = response.json()
                    result["response_data"] = response_data
                    if isinstance(response_data, dict) and "courses" in response_data:
                        self.print_colored(
                            f"   📊 Cursos encontrados: {len(response_data['courses'])}",
                            "cyan",
                        )

                except json.JSONDecodeError:
                    result["response_text"] = response.text[:200]

            else:
                self.print_colored(f"   ❌ Falha: {response.status_code}", "red")
                try:
                    error_data = response.json()
                    result["error"] = error_data
                    self.print_colored(f"      Detalhes: {error_data}", "yellow")
                except json.JSONDecodeError:
                    result["error"] = response.text
                    self.print_colored(
                        f"      Resposta: {response.text[:200]}", "yellow"
                    )

        except requests.exceptions.RequestException as e:
            self.print_colored(f"   ❌ Erro na requisição: {e}", "red")
            result = {
                "endpoint_key": endpoint_key,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

        self.results.append(result)
        return result

    def run_tests(self, endpoints_to_test: list[str] | None = None) -> None:
        """
        Executa os testes para os endpoints especificados.
        """
        self.print_header("Iniciando Testes de Endpoints de Cursos")

        if not endpoints_to_test:
            endpoints_to_test = list(ENDPOINTS.keys())

        for endpoint_key in endpoints_to_test:
            self.test_endpoint(endpoint_key)
            print("-" * 60)

        self.save_report()

    def save_report(self) -> None:
        """Salva o relatório de testes em um arquivo JSON."""
        if not os.path.exists(REPORTS_DIR):
            os.makedirs(REPORTS_DIR)

        report_filename = f"courses_test_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        report_path = os.path.join(REPORTS_DIR, report_filename)

        summary = {
            "total_tests": len(self.results),
            "successful_tests": sum(1 for r in self.results if r["success"]),
            "failed_tests": sum(1 for r in self.results if not r["success"]),
            "test_run_at": datetime.now().isoformat(),
        }

        report_data = {"summary": summary, "results": self.results}

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        self.print_header("Relatório de Testes")
        self.print_colored(f"📄 Relatório salvo em: {report_path}", "green")
        self.print_colored(json.dumps(summary, indent=2, ensure_ascii=False), "white")


def list_endpoints() -> None:
    """Lista os endpoints disponíveis para teste."""
    tester = QuickCoursesTester()
    tester.print_header("Endpoints de Cursos Disponíveis para Teste")
    for key, config in ENDPOINTS.items():
        tester.print_colored(f"- {key}:", "cyan")
        tester.print_colored(f"  Descrição: {config['description']}", "white")
        tester.print_colored(f"  Endpoint: {config['method']} {config['url']}", "white")
        if "params" in config:
            tester.print_colored(f"  Parâmetros: {config['params']}", "white")


def main() -> None:
    """Função principal para executar o script de teste."""
    parser = argparse.ArgumentParser(
        description="Script de teste rápido para endpoints de cursos do Portal KNN."
    )
    parser.add_argument(
        "--all", action="store_true", help="Testar todos os endpoints de cursos."
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        help="Testar um endpoint específico pelo nome (ex: courses_english).",
    )
    parser.add_argument(
        "--list", action="store_true", help="Listar todos os endpoints disponíveis."
    )

    args = parser.parse_args()
    tester = QuickCoursesTester()

    if args.list:
        list_endpoints()
    elif args.all:
        tester.run_tests()
    elif args.endpoint:
        if args.endpoint in ENDPOINTS:
            tester.run_tests([args.endpoint])
        else:
            tester.print_colored(
                f"❌ Endpoint '{args.endpoint}' não encontrado.", "red"
            )
            list_endpoints()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
