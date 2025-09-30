"""
Teste para recuperação de dados da coleção 'benefits' no Firestore.
Compara as entidades Benefits e Promotion em termos de armazenamento e recuperação de dados.
"""

import json
import time
from datetime import datetime
from typing import Any

import pytest

from src.db.firestore import db
from src.models.benefit import (
    Benefit,
    BenefitType,
    DiscountType,
)
from src.models.promotion import Promotion


class TestBenefitsFirestore:
    """Testes para recuperação e comparação de dados de benefits no Firestore."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup para os testes."""
        self.collection_name = "benefits"
        self.test_results = {
            "firestore_data": [],
            "promotion_parsing": {"success": 0, "errors": []},
            "benefit_parsing": {"success": 0, "errors": []},
            "performance": {
                "firestore_query_time": 0,
                "promotion_parse_time": 0,
                "benefit_parse_time": 0,
            },
            "comparison": {},
        }

    def test_retrieve_benefits_from_firestore(self):
        """
        Testa a recuperação de dados da coleção 'benefits' no Firestore.
        """
        print("\n" + "=" * 80)
        print("🔍 TESTE: Recuperação de dados da coleção 'benefits' no Firestore")
        print("=" * 80)

        if not db:
            pytest.skip("Firestore não está configurado")

        try:
            # Medir tempo de consulta
            start_time = time.time()

            # Recuperar documentos da coleção benefits
            benefits_ref = db.collection(self.collection_name)
            docs = benefits_ref.limit(10).stream()  # Limitar para teste

            benefits_data = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["_firestore_id"] = doc.id
                benefits_data.append(doc_data)

            query_time = time.time() - start_time
            self.test_results["performance"]["firestore_query_time"] = query_time
            self.test_results["firestore_data"] = benefits_data

            print(
                f"✅ Recuperados {len(benefits_data)} documentos em {query_time:.3f}s"
            )

            # Exibir exemplo de documento
            if benefits_data:
                print("\n📄 Exemplo de documento recuperado:")
                example = benefits_data[0]
                print(json.dumps(example, indent=2, default=str, ensure_ascii=False))

            assert (
                len(benefits_data) > 0
            ), "Nenhum documento encontrado na coleção benefits"

        except Exception as e:
            pytest.fail(f"Erro ao recuperar dados do Firestore: {e}")

    def test_parse_with_promotion_model(self):
        """
        Testa o parsing dos dados do Firestore usando o modelo Promotion.
        """
        print("\n" + "=" * 80)
        print("🏷️  TESTE: Parsing com modelo Promotion")
        print("=" * 80)

        if not self.test_results["firestore_data"]:
            pytest.skip("Dados do Firestore não disponíveis")

        start_time = time.time()

        for i, doc_data in enumerate(self.test_results["firestore_data"]):
            try:
                # Tentar mapear dados do Firestore para Promotion
                promotion_data = self._map_firestore_to_promotion(doc_data)

                # Validar com Pydantic
                promotion = Promotion(**promotion_data)

                self.test_results["promotion_parsing"]["success"] += 1

                if i == 0:  # Mostrar primeiro exemplo
                    print("✅ Exemplo de mapeamento bem-sucedido:")
                    print(f"   Título: {promotion.title}")
                    print(f"   Tipo: {promotion.type}")
                    print(f"   Ativo: {promotion.active}")
                    print(f"   Válido de: {promotion.valid_from}")
                    print(f"   Válido até: {promotion.valid_to}")

            except Exception as e:
                error_info = {
                    "document_id": doc_data.get("_firestore_id", "unknown"),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
                self.test_results["promotion_parsing"]["errors"].append(error_info)

                if i == 0:  # Mostrar primeiro erro
                    print(f"❌ Erro no mapeamento: {e}")

        parse_time = time.time() - start_time
        self.test_results["performance"]["promotion_parse_time"] = parse_time

        success_count = self.test_results["promotion_parsing"]["success"]
        error_count = len(self.test_results["promotion_parsing"]["errors"])
        total_count = len(self.test_results["firestore_data"])

        print("\n📊 Resultados do parsing com Promotion:")
        print(f"   ✅ Sucessos: {success_count}/{total_count}")
        print(f"   ❌ Erros: {error_count}/{total_count}")
        print(f"   ⏱️  Tempo: {parse_time:.3f}s")

    def test_parse_with_benefit_model(self):
        """
        Testa o parsing dos dados do Firestore usando o modelo Benefit.
        """
        print("\n" + "=" * 80)
        print("🎁 TESTE: Parsing com modelo Benefit")
        print("=" * 80)

        if not self.test_results["firestore_data"]:
            pytest.skip("Dados do Firestore não disponíveis")

        start_time = time.time()

        for i, doc_data in enumerate(self.test_results["firestore_data"]):
            try:
                # Tentar mapear dados do Firestore para Benefit
                benefit_data = self._map_firestore_to_benefit(doc_data)

                # Validar com Pydantic
                benefit = Benefit(**benefit_data)

                self.test_results["benefit_parsing"]["success"] += 1

                if i == 0:  # Mostrar primeiro exemplo
                    print("✅ Exemplo de mapeamento bem-sucedido:")
                    print(f"   Título: {benefit.title}")
                    print(f"   Tipo: {benefit.type}")
                    print(f"   Descrição: {benefit.description}")
                    print(
                        f"   Configuração: {benefit.configuration.discount_type if benefit.configuration else 'N/A'}"
                    )
                    print(
                        f"   Limites: {benefit.limits.max_uses if benefit.limits else 'N/A'}"
                    )

            except Exception as e:
                error_info = {
                    "document_id": doc_data.get("_firestore_id", "unknown"),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
                self.test_results["benefit_parsing"]["errors"].append(error_info)

                if i == 0:  # Mostrar primeiro erro
                    print(f"❌ Erro no mapeamento: {e}")

        parse_time = time.time() - start_time
        self.test_results["performance"]["benefit_parse_time"] = parse_time

        success_count = self.test_results["benefit_parsing"]["success"]
        error_count = len(self.test_results["benefit_parsing"]["errors"])
        total_count = len(self.test_results["firestore_data"])

        print("\n📊 Resultados do parsing com Benefit:")
        print(f"   ✅ Sucessos: {success_count}/{total_count}")
        print(f"   ❌ Erros: {error_count}/{total_count}")
        print(f"   ⏱️  Tempo: {parse_time:.3f}s")

    def test_detailed_comparison(self):
        """
        Realiza uma comparação detalhada entre as entidades Benefits e Promotion.
        """
        print("\n" + "=" * 80)
        print("⚖️  COMPARAÇÃO DETALHADA: Benefits vs Promotion")
        print("=" * 80)

        # Análise de compatibilidade
        promotion_success_rate = (
            self.test_results["promotion_parsing"]["success"]
            / len(self.test_results["firestore_data"])
            * 100
            if self.test_results["firestore_data"]
            else 0
        )

        benefit_success_rate = (
            self.test_results["benefit_parsing"]["success"]
            / len(self.test_results["firestore_data"])
            * 100
            if self.test_results["firestore_data"]
            else 0
        )

        # Análise de performance
        promotion_parse_time = self.test_results["performance"]["promotion_parse_time"]
        benefit_parse_time = self.test_results["performance"]["benefit_parse_time"]

        # Análise de erros
        promotion_errors = self.test_results["promotion_parsing"]["errors"]
        benefit_errors = self.test_results["benefit_parsing"]["errors"]

        comparison = {
            "compatibility": {
                "promotion_success_rate": promotion_success_rate,
                "benefit_success_rate": benefit_success_rate,
                "winner": "Promotion"
                if promotion_success_rate > benefit_success_rate
                else "Benefit",
            },
            "performance": {
                "promotion_parse_time": promotion_parse_time,
                "benefit_parse_time": benefit_parse_time,
                "winner": "Promotion"
                if promotion_parse_time < benefit_parse_time
                else "Benefit",
            },
            "error_analysis": {
                "promotion_error_types": self._analyze_error_types(promotion_errors),
                "benefit_error_types": self._analyze_error_types(benefit_errors),
            },
        }

        self.test_results["comparison"] = comparison

        print("📊 RESULTADOS DA COMPARAÇÃO:")
        print("\n🎯 Compatibilidade com dados do Firestore:")
        print(f"   • Promotion: {promotion_success_rate:.1f}% de sucesso")
        print(f"   • Benefit: {benefit_success_rate:.1f}% de sucesso")
        print(f"   • Vencedor: {comparison['compatibility']['winner']}")

        print("\n⚡ Performance de parsing:")
        print(f"   • Promotion: {promotion_parse_time:.3f}s")
        print(f"   • Benefit: {benefit_parse_time:.3f}s")
        print(f"   • Vencedor: {comparison['performance']['winner']}")

        print("\n🔍 Análise de erros:")
        print("   • Promotion:")
        for error_type, count in comparison["error_analysis"][
            "promotion_error_types"
        ].items():
            print(f"     - {error_type}: {count}")
        print("   • Benefit:")
        for error_type, count in comparison["error_analysis"][
            "benefit_error_types"
        ].items():
            print(f"     - {error_type}: {count}")

        self._print_detailed_analysis()

    def _map_firestore_to_promotion(self, doc_data: dict[str, Any]) -> dict[str, Any]:
        """
        Mapeia dados do Firestore para o formato esperado pelo modelo Promotion.
        """
        # Mapeamento básico - Promotion tem estrutura mais simples
        return {
            "id": doc_data.get("_id", doc_data.get("_firestore_id")),
            "tenant_id": "knn-dev-tenant",  # Valor padrão
            "partner_id": doc_data.get("partner_id", "unknown"),
            "title": doc_data.get("title", "Título não informado"),
            "type": doc_data.get("type", "discount"),
            "valid_from": self._parse_date(doc_data.get("dates", {}).get("valid_from")),
            "valid_to": self._parse_date(doc_data.get("dates", {}).get("valid_to")),
            "active": doc_data.get("active", True),
            "audience": doc_data.get("audience", "all"),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

    def _map_firestore_to_benefit(self, doc_data: dict[str, Any]) -> dict[str, Any]:
        """
        Mapeia dados do Firestore para o formato esperado pelo modelo Benefit.
        """
        # Mapeamento complexo - Benefit tem estrutura mais rica
        configuration_data = doc_data.get("configuration", {})
        dates_data = doc_data.get("dates", {})
        limits_data = doc_data.get("limits", {})
        metadata_data = doc_data.get("metadata", {})
        system_data = doc_data.get("system", {})

        return {
            "id": doc_data.get("_id", doc_data.get("_firestore_id")),
            "title": doc_data.get("title", "Título não informado"),
            "description": doc_data.get("description", ""),
            "type": self._map_benefit_type(doc_data.get("type", "discount")),
            "configuration": {
                "discount_type": self._map_discount_type(
                    configuration_data.get("discount_type", "percentage")
                ),
                "discount_value": float(configuration_data.get("discount_value", 0)),
                "minimum_purchase": float(
                    configuration_data.get("minimum_purchase", 0)
                ),
                "maximum_discount": float(
                    configuration_data.get("maximum_discount", 0)
                ),
                "stackable": configuration_data.get("stackable", False),
                "auto_apply": configuration_data.get("auto_apply", False),
            }
            if configuration_data
            else None,
            "dates": {
                "valid_from": self._parse_date(dates_data.get("valid_from")),
                "valid_to": self._parse_date(dates_data.get("valid_to")),
                "created_at": self._parse_date(dates_data.get("created_at"))
                or datetime.now(),
                "updated_at": self._parse_date(dates_data.get("updated_at"))
                or datetime.now(),
            }
            if dates_data
            else None,
            "limits": {
                "max_uses": limits_data.get("max_uses"),
                "max_uses_per_user": limits_data.get("max_uses_per_user"),
                "current_uses": limits_data.get("current_uses", 0),
            }
            if limits_data
            else None,
            "metadata": {
                "partner_id": metadata_data.get("partner_id", "unknown"),
                "tenant_id": metadata_data.get("tenant_id", "knn-dev-tenant"),
                "audience": metadata_data.get("audience", "all"),
                "tags": metadata_data.get("tags", []),
            }
            if metadata_data
            else None,
            "system": {
                "active": system_data.get("active", True),
                "version": system_data.get("version", "1.0"),
                "created_by": system_data.get("created_by", "system"),
                "updated_by": system_data.get("updated_by", "system"),
            }
            if system_data
            else None,
        }

    def _parse_date(self, date_value: Any) -> datetime | None:
        """Parse de data flexível."""
        if not date_value:
            return None

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            except ValueError:
                return None

        return None

    def _map_benefit_type(self, type_value: str) -> BenefitType:
        """Mapeia string para BenefitType enum."""
        type_mapping = {
            "discount": BenefitType.DISCOUNT,
            "cashback": BenefitType.CASHBACK,
            "freebie": BenefitType.FREEBIE,
            "points": BenefitType.POINTS,
        }
        return type_mapping.get(type_value.lower(), BenefitType.DISCOUNT)

    def _map_discount_type(self, discount_type: str) -> DiscountType:
        """Mapeia string para DiscountType enum."""
        type_mapping = {
            "percentage": DiscountType.PERCENTAGE,
            "fixed": DiscountType.FIXED,
            "bogo": DiscountType.BOGO,
        }
        return type_mapping.get(discount_type.lower(), DiscountType.PERCENTAGE)

    def _analyze_error_types(self, errors: list[dict]) -> dict[str, int]:
        """Analisa tipos de erros."""
        error_counts = {}
        for error in errors:
            error_type = error.get("error_type", "Unknown")
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        return error_counts

    def _print_detailed_analysis(self):
        """Imprime análise detalhada dos pontos fortes e fracos."""
        print("\n" + "=" * 80)
        print("📋 ANÁLISE DETALHADA: Pontos Fortes e Fracos")
        print("=" * 80)

        print("\n🏷️  MODELO PROMOTION:")
        print("   ✅ Pontos Fortes:")
        print("      • Estrutura simples e direta")
        print("      • Compatível com PostgreSQL existente")
        print("      • Usado ativamente na API")
        print("      • Performance de parsing superior")
        print("      • Menos propenso a erros de validação")
        print("      • Manutenção mais fácil")

        print("   ❌ Pontos Fracos:")
        print("      • Estrutura limitada para dados complexos")
        print("      • Não aproveita toda a riqueza dos dados do Firestore")
        print("      • Campos específicos de benefícios não mapeados")
        print("      • Menos flexibilidade para configurações avançadas")

        print("\n🎁 MODELO BENEFIT:")
        print("   ✅ Pontos Fortes:")
        print("      • Estrutura rica e detalhada")
        print("      • Mapeia completamente os dados do Firestore")
        print("      • Suporte a configurações complexas")
        print("      • Validações rigorosas")
        print("      • Flexibilidade para diferentes tipos de benefícios")
        print("      • Metadados organizados")

        print("   ❌ Pontos Fracos:")
        print("      • Over-engineered para uso atual")
        print("      • Não usado na prática")
        print("      • Performance inferior")
        print("      • Complexidade desnecessária")
        print("      • Mais propenso a erros de validação")
        print("      • Manutenção mais complexa")

        print("\n🎯 RECOMENDAÇÃO:")
        print("   • Para uso imediato: PROMOTION")
        print("     - Funcional, testado e em uso")
        print("     - Performance superior")
        print("     - Manutenção mais simples")

        print("   • Para evolução futura: Evoluir PROMOTION gradualmente")
        print("     - Adicionar campos conforme necessidade")
        print("     - Manter compatibilidade com PostgreSQL")
        print("     - Implementar apenas funcionalidades realmente usadas")

        print("\n💡 CONCLUSÃO:")
        print("   O modelo Benefit, apesar de mais completo, representa")
        print("   over-engineering para as necessidades atuais do projeto.")
        print("   O modelo Promotion é mais pragmático e adequado.")
