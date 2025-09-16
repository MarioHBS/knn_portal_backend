"""Suite de testes consolidada para o Portal de Benefícios KNN.

Combina testes de endpoints, validação de audience e outras funcionalidades
para facilitar a execução de testes de forma organizada.
"""

import sys
from pathlib import Path

import requests

# Adicionar o diretório raiz ao path para imports
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from src.models.promotion import Promotion
from src.utils.logging import logger


class TestSuite:
    """Suite consolidada de testes."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []

    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Registra resultado de um teste."""
        status = "✓ PASS" if success else "✗ FAIL"
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"

        self.test_results.append((test_name, success, message))
        logger.info(result)

    def test_audience_validation(self):
        """Testa validação do modelo Pydantic para audience."""
        logger.info("=== Testando Validação de Audience ===")

        # Teste 1: Audience válido
        try:
            valid_promotion = Promotion(
                id="test_promo_1",
                title="Promoção Teste",
                description="Descrição teste",
                discount_percentage=10.0,
                audience=["ENSINO_MEDIO", "GRADUACAO"],
            )
            self.log_test_result("Audience válido", True, "Ensino Médio e Graduação")
        except Exception as e:
            self.log_test_result("Audience válido", False, str(e))

        # Teste 2: Audience inválido
        try:
            invalid_promotion = Promotion(
                id="test_promo_2",
                title="Promoção Teste",
                description="Descrição teste",
                discount_percentage=10.0,
                audience=["CURSO_INVALIDO"],
            )
            self.log_test_result("Audience inválido", False, "Deveria ter falhado")
        except Exception:
            self.log_test_result("Audience inválido", True, "Validação funcionou")

    def test_endpoints(self):
        """Testa endpoints do Portal de Benefícios."""
        logger.info("=== Testando Endpoints ===")

        endpoints = [
            {
                "name": "Health Check",
                "method": "GET",
                "url": f"{self.base_url}/health",
                "expected_status": 200,
            },
            {
                "name": "Listar Cursos",
                "method": "GET",
                "url": f"{self.base_url}/courses",
                "expected_status": 200,
            },
            {
                "name": "Listar Promoções",
                "method": "GET",
                "url": f"{self.base_url}/promotions",
                "expected_status": 200,
            },
            {
                "name": "Buscar Aluno",
                "method": "GET",
                "url": f"{self.base_url}/students/search",
                "params": {"cpf": "12345678901"},
                "expected_status": [200, 404],  # Pode não encontrar
            },
        ]

        for endpoint in endpoints:
            try:
                if endpoint["method"] == "GET":
                    response = requests.get(
                        endpoint["url"], params=endpoint.get("params", {}), timeout=10
                    )

                expected = endpoint["expected_status"]
                if isinstance(expected, list):
                    success = response.status_code in expected
                else:
                    success = response.status_code == expected

                message = f"Status: {response.status_code}"
                if success and response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            message += f", Items: {len(data)}"
                        elif isinstance(data, dict):
                            if "data" in data and isinstance(data["data"], list):
                                message += f", Items: {len(data['data'])}"
                            elif "items" in data:
                                message += f", Items: {len(data['items'])}"
                    except:
                        pass

                self.log_test_result(endpoint["name"], success, message)

            except requests.exceptions.ConnectionError:
                self.log_test_result(
                    endpoint["name"], False, "Servidor não está rodando"
                )
            except Exception as e:
                self.log_test_result(endpoint["name"], False, str(e))

    def test_promotion_filtering(self):
        """Testa filtragem de promoções por audience."""
        logger.info("=== Testando Filtragem de Promoções ===")

        try:
            # Buscar promoções com filtro de curso
            response = requests.get(
                f"{self.base_url}/promotions",
                params={"course_code": "EM"},  # Ensino Médio
                timeout=10,
            )

            if response.status_code == 200:
                promotions = response.json()
                if isinstance(promotions, dict) and "items" in promotions:
                    promotions = promotions["items"]

                # Verificar se todas as promoções retornadas são válidas para EM
                valid_promotions = 0
                for promo in promotions:
                    if "audience" in promo and "EM" in promo["audience"]:
                        valid_promotions += 1

                success = valid_promotions == len(promotions)
                message = f"{valid_promotions}/{len(promotions)} promoções válidas"
                self.log_test_result("Filtragem por curso", success, message)
            else:
                self.log_test_result(
                    "Filtragem por curso", False, f"Status: {response.status_code}"
                )

        except requests.exceptions.ConnectionError:
            self.log_test_result(
                "Filtragem por curso", False, "Servidor não está rodando"
            )
        except Exception as e:
            self.log_test_result("Filtragem por curso", False, str(e))

    def run_all_tests(self):
        """Executa todos os testes da suite."""
        logger.info("🚀 Iniciando Suite de Testes do Portal de Benefícios KNN")
        logger.info("=" * 60)

        # Executar todos os testes
        self.test_audience_validation()
        self.test_endpoints()
        self.test_promotion_filtering()

        # Resumo dos resultados
        logger.info("=" * 60)
        logger.info("📊 RESUMO DOS TESTES")

        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success, _ in self.test_results if success)
        failed_tests = total_tests - passed_tests

        logger.info(f"Total de testes: {total_tests}")
        logger.info(f"✓ Passou: {passed_tests}")
        logger.info(f"✗ Falhou: {failed_tests}")

        if failed_tests > 0:
            logger.info("\n❌ TESTES QUE FALHARAM:")
            for test_name, success, message in self.test_results:
                if not success:
                    logger.info(f"  - {test_name}: {message}")

        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        logger.info(f"\n📈 Taxa de sucesso: {success_rate:.1f}%")

        return failed_tests == 0


def main():
    """Função principal."""
    base_url = "http://localhost:8000"

    if len(sys.argv) > 1:
        if sys.argv[1].startswith("http"):
            base_url = sys.argv[1]
        elif sys.argv[1] in ["--help", "-h"]:
            print("Uso: python test_suite.py [URL_BASE]")
            print("  URL_BASE: URL do servidor (padrão: http://localhost:8000)")
            print("\nExemplos:")
            print("  python test_suite.py")
            print("  python test_suite.py http://localhost:8000")
            return

    test_suite = TestSuite(base_url)
    success = test_suite.run_all_tests()

    # Exit code baseado no resultado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
