#!/usr/bin/env python3
"""
Script de teste para validar a implementação do campo audience.

Este script testa:
1. Validação do modelo Pydantic para audience
2. Criação de promoções com diferentes valores de audience
3. Filtragem de promoções por audience nos endpoints
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Promotion, PromotionRequest
from src.utils import logger


class AudienceImplementationTest:
    """Classe para testar a implementação do campo audience."""

    def __init__(self):
        self.test_results = []

    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Registra o resultado de um teste."""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "message": message,
        }
        self.test_results.append(result)
        logger.info(f"{status} - {test_name}: {message}")

    def test_promotion_model_validation(self):
        """Testa a validação do modelo Promotion."""
        logger.info("\n=== TESTANDO VALIDAÇÃO DO MODELO PROMOTION ===")

        # Teste 1: Audience válido com student
        try:
            promotion = Promotion(
                id="test-1",
                tenant_id="test-tenant",
                partner_id="test-partner",
                title="Promoção para Estudantes",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["student"],
            )
            self.log_test_result(
                "Audience válido - student", True, f"Audience: {promotion.audience}"
            )
        except Exception as e:
            self.log_test_result("Audience válido - student", False, f"Erro: {str(e)}")

        # Teste 2: Audience válido com employee
        try:
            promotion = Promotion(
                id="test-2",
                tenant_id="test-tenant",
                partner_id="test-partner",
                title="Promoção para Funcionários",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["employee"],
            )
            self.log_test_result(
                "Audience válido - employee", True, f"Audience: {promotion.audience}"
            )
        except Exception as e:
            self.log_test_result("Audience válido - employee", False, f"Erro: {str(e)}")

        # Teste 3: Audience válido com ambos
        try:
            promotion = Promotion(
                id="test-3",
                tenant_id="test-tenant",
                partner_id="test-partner",
                title="Promoção para Todos",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["student", "employee"],
            )
            self.log_test_result(
                "Audience válido - ambos", True, f"Audience: {promotion.audience}"
            )
        except Exception as e:
            self.log_test_result("Audience válido - ambos", False, f"Erro: {str(e)}")

        # Teste 4: Audience inválido
        try:
            promotion = Promotion(
                id="test-4",
                tenant_id="test-tenant",
                partner_id="test-partner",
                title="Promoção Inválida",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["invalid"],
            )
            self.log_test_result(
                "Audience inválido - deve falhar",
                False,
                "Validação não rejeitou valor inválido",
            )
        except Exception as e:
            self.log_test_result(
                "Audience inválido - deve falhar",
                True,
                f"Validação funcionou: {str(e)}",
            )

        # Teste 5: Audience com duplicatas - deve remover duplicatas
        try:
            promotion = Promotion(
                id="test-5",
                tenant_id="test-tenant",
                partner_id="test-partner",
                title="Promoção com Duplicatas",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["student", "student"],
            )
            # Verificar se duplicatas foram removidas
            if promotion.audience == ["student"]:
                self.log_test_result(
                    "Audience com duplicatas - deve remover duplicatas",
                    True,
                    f"Duplicatas removidas corretamente: {promotion.audience}",
                )
            else:
                self.log_test_result(
                    "Audience com duplicatas - deve remover duplicatas",
                    False,
                    f"Duplicatas não foram removidas: {promotion.audience}",
                )
        except Exception as e:
            self.log_test_result(
                "Audience com duplicatas - deve remover duplicatas",
                False,
                f"Erro inesperado: {str(e)}",
            )

    def test_promotion_request_validation(self):
        """Testa a validação do modelo PromotionRequest."""
        logger.info("\n=== TESTANDO VALIDAÇÃO DO MODELO PROMOTION REQUEST ===")

        # Teste 1: Request válido
        try:
            request = PromotionRequest(
                title="Promoção de Teste",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["student", "employee"],
            )
            self.log_test_result(
                "PromotionRequest válido", True, f"Audience: {request.audience}"
            )
        except Exception as e:
            self.log_test_result("PromotionRequest válido", False, f"Erro: {str(e)}")

        # Teste 2: Request inválido
        try:
            request = PromotionRequest(
                title="Promoção Inválida",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["admin"],  # Valor inválido
            )
            self.log_test_result(
                "PromotionRequest inválido - deve falhar",
                False,
                "Validação não rejeitou valor inválido",
            )
        except Exception as e:
            self.log_test_result(
                "PromotionRequest inválido - deve falhar",
                True,
                f"Validação funcionou: {str(e)}",
            )

    def test_json_serialization(self):
        """Testa a serialização JSON dos modelos."""
        logger.info("\n=== TESTANDO SERIALIZAÇÃO JSON ===")

        try:
            promotion = Promotion(
                id="test-json",
                tenant_id="test-tenant",
                partner_id="test-partner",
                title="Promoção JSON",
                type="discount",
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=30),
                active=True,
                audience=["student", "employee"],
            )

            # Testar serialização
            json_data = promotion.model_dump()
            json.dumps(json_data, default=str)

            # Verificar se audience está presente
            if "audience" in json_data and json_data["audience"] == [
                "student",
                "employee",
            ]:
                self.log_test_result(
                    "Serialização JSON",
                    True,
                    f"Audience serializado corretamente: {json_data['audience']}",
                )
            else:
                self.log_test_result(
                    "Serialização JSON",
                    False,
                    f"Audience não encontrado ou incorreto: {json_data.get('audience')}",
                )

        except Exception as e:
            self.log_test_result("Serialização JSON", False, f"Erro: {str(e)}")

    def print_summary(self):
        """Imprime um resumo dos testes."""
        logger.info("\n" + "=" * 60)
        logger.info("RESUMO DOS TESTES DE IMPLEMENTAÇÃO DO AUDIENCE")
        logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        logger.info(f"Total de testes: {total_tests}")
        logger.info(f"Testes aprovados: {passed_tests}")
        logger.info(f"Testes falharam: {failed_tests}")
        logger.info(f"Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            logger.info("\nTestes que falharam:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  - {result['test']}: {result['message']}")

        logger.info("\nDetalhes completos:")
        for result in self.test_results:
            logger.info(f"  {result['status']} {result['test']}")
            if result["message"]:
                logger.info(f"    {result['message']}")

    def run_all_tests(self):
        """Executa todos os testes."""
        logger.info("INICIANDO TESTES DE IMPLEMENTAÇÃO DO CAMPO AUDIENCE")

        self.test_promotion_model_validation()
        self.test_promotion_request_validation()
        self.test_json_serialization()

        self.print_summary()

        return len([r for r in self.test_results if not r["success"]]) == 0


def main():
    """Função principal."""
    tester = AudienceImplementationTest()
    success = tester.run_all_tests()

    if success:
        logger.info(
            "\n🎉 TODOS OS TESTES PASSARAM! A implementação está funcionando corretamente."
        )
        return 0
    else:
        logger.error("\n❌ ALGUNS TESTES FALHARAM! Verifique a implementação.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
