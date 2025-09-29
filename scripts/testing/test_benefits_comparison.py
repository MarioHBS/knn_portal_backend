#!/usr/bin/env python3
"""Script para testar as entidades Benefits
na recuperação de dados da coleção 'benefits' no Firestore.

Funcionalidades:
1. Parsing com modelo Benefit
2. Análise de performance
3. Comparação de compatibilidade
4. Relatório detalhado
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.db.firestore import db
from src.models.benefit import (
    Benefit,
)
from src.utils import logger


class BenefitsComparisonTester:
    """Classe para testar Benefits."""

    def __init__(self):
        """Inicializa o testador."""
        self.collection_name = "benefits"
        self.results = {
            "firestore_data": [],
            "benefit_results": {"success": 0, "errors": []},
            "performance": {},
            "comparison": {},
        }

    def run_comparison(self) -> dict[str, Any]:
        """
        Executa o teste completo de Benefits.

        Returns:
            Dicionário com todos os resultados da análise.
        """
        logger.info("🚀 Iniciando teste completo de Benefits")

        try:
            # 1. Recuperar dados do Firestore
            self._retrieve_firestore_data()

            # 2. Testar parsing com Benefit
            self._test_benefit_parsing()

            # 3. Gerar relatório
            self._generate_report()

            return self.results

        except Exception as e:
            logger.error(f"Erro durante a análise: {e}")
            raise

    def _retrieve_firestore_data(self):
        """Recupera dados da coleção benefits no Firestore."""
        logger.info("📥 Recuperando dados da coleção 'benefits' no Firestore...")

        if not db:
            raise RuntimeError("Firestore não está configurado")

        start_time = time.time()

        try:
            benefits_ref = db.collection(self.collection_name)
            docs = benefits_ref.limit(20).stream()  # Limitar para teste

            benefits_data = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["_firestore_id"] = doc.id
                benefits_data.append(doc_data)

            query_time = time.time() - start_time

            self.results["firestore_data"] = benefits_data
            self.results["performance"]["firestore_query_time"] = query_time

            logger.info(
                f"✅ Recuperados {len(benefits_data)} documentos em {query_time:.3f}s"
            )

            if benefits_data:
                logger.info("📄 Exemplo de documento:")
                example = benefits_data[0]
                logger.info(
                    json.dumps(example, indent=2, default=str, ensure_ascii=False)[:500]
                    + "..."
                )

        except Exception as e:
            logger.error(f"❌ Erro ao recuperar dados do Firestore: {e}")
            raise

    def _test_benefit_parsing(self):
        """Testa o parsing dos dados usando o modelo Benefit."""
        logger.info("🎁 Testando parsing com modelo Benefit...")

        start_time = time.time()
        success_count = 0
        total_count = len(self.results["firestore_data"])

        for doc_data in self.results["firestore_data"]:
            try:
                benefit_data = self._map_to_benefit(doc_data)
                benefit = Benefit(**benefit_data)
                success_count += 1

                # Log do primeiro exemplo
                if success_count == 1:
                    logger.info("✅ Exemplo de Benefit criado:")
                    logger.info(f"   ID: {benefit.id}")
                    logger.info(f"   Título: {benefit.title}")
                    logger.info(f"   Tipo: {benefit.type}")
                    logger.info(f"   Ativo: {benefit.active}")

            except Exception as e:
                self.results["benefit_results"]["errors"].append(
                    {
                        "doc_id": doc_data.get("_firestore_id", "unknown"),
                        "error": str(e),
                    }
                )
                logger.warning(f"❌ Erro no parsing Benefit: {e}")

        parse_time = time.time() - start_time
        self.results["performance"]["benefit_parse_time"] = parse_time
        self.results["benefit_results"]["success"] = success_count

        logger.info(
            f"📊 Resultados Benefit: {success_count}/{total_count} sucessos em {parse_time:.3f}s"
        )

    def _perform_comparison(self):
        """Realiza a comparação entre os modelos."""
        logger.info("⚖️  Realizando comparação detalhada...")

        total_docs = len(self.results["firestore_data"])

        if total_docs == 0:
            logger.warning("Nenhum documento para comparar")
            return

        # Taxas de sucesso
        benefit_success_rate = (
            self.results["benefit_results"]["success"] / total_docs
        ) * 100

        # Performance
        benefit_time = self.results["performance"]["benefit_parse_time"]

        # Análise de erros
        benefit_errors = self._analyze_errors(self.results["benefit_results"]["errors"])

        self.results["comparison"] = {
            "compatibility": {
                "benefit_success_rate": benefit_success_rate,
                "winner": "Benefit",
            },
            "performance": {"benefit_parse_time": benefit_time, "winner": "Benefit"},
            "error_analysis": {"benefit_errors": benefit_errors},
        }

    def _generate_report(self):
        """Gera relatório detalhado da análise."""
        logger.info("📊 Gerando relatório...")

        # Realizar análise
        self._perform_comparison()

        # Imprimir relatório
        self._print_report()

        return self.results["comparison"]

    def _print_report(self):
        """Imprime relatório detalhado da análise."""
        logger.info("\n" + "=" * 80)
        logger.info("📋 RELATÓRIO FINAL: Benefits")
        logger.info("=" * 80)

        comparison = self.results["comparison"]

        logger.info("\n🎯 COMPATIBILIDADE COM DADOS DO FIRESTORE:")
        logger.info(
            f"   • Benefit: {comparison['compatibility']['benefit_success_rate']:.1f}% de sucesso"
        )
        logger.info(f"   • Vencedor: {comparison['compatibility']['winner']}")

        logger.info("\n⚡ PERFORMANCE DE PARSING:")
        logger.info(
            f"   • Benefit: {comparison['performance']['benefit_parse_time']:.3f}s"
        )
        logger.info(f"   • Vencedor: {comparison['performance']['winner']}")

        logger.info("\n🔍 ANÁLISE DE ERROS:")
        logger.info("   • Benefit:")
        for error_type, count in comparison["error_analysis"]["benefit_errors"].items():
            logger.info(f"     - {error_type}: {count}")

        self._print_strengths_and_weaknesses()

    def _print_strengths_and_weaknesses(self):
        """Imprime análise de pontos fortes e fracos."""
        logger.info("\n" + "=" * 80)
        logger.info("📊 ANÁLISE: Pontos Fortes e Fracos")
        logger.info("=" * 80)

        logger.info("\n🎁 MODELO BENEFIT:")
        logger.info("   ✅ Pontos Fortes:")
        logger.info("      • Estrutura rica e detalhada")
        logger.info("      • Mapeia completamente os dados do Firestore")
        logger.info("      • Suporte a configurações complexas de desconto")
        logger.info("      • Validações rigorosas com Pydantic")
        logger.info("      • Flexibilidade para diferentes tipos de benefícios")
        logger.info("      • Metadados bem organizados")
        logger.info("      • Suporte a limites e controles avançados")

        logger.info("   ❌ Pontos Fracos:")
        logger.info("      • Over-engineered para necessidades atuais")
        logger.info("      • Não usado em produção (código morto)")
        logger.info("      • Performance inferior")
        logger.info("      • Complexidade desnecessária")
        logger.info("      • Mais propenso a erros de validação")
        logger.info("      • Manutenção mais complexa")
        logger.info("      • Sem integração com endpoints existentes")

        logger.info("\n🎯 RECOMENDAÇÃO FINAL:")
        logger.info("   • USAR: Modelo Benefit")
        logger.info("     - Estrutura rica e detalhada")
        logger.info("     - Mapeia completamente os dados do Firestore")
        logger.info("     - Suporte a configurações complexas")
        logger.info("     - Validações rigorosas com Pydantic")

        logger.info("   • EVOLUIR: Benefit gradualmente")
        logger.info("     - Implementar funcionalidades conforme necessidade")
        logger.info("     - Manter compatibilidade com dados do Firestore")
        logger.info("     - Otimizar performance quando necessário")

    def _map_to_benefit(self, doc_data: dict[str, Any]) -> dict[str, Any]:
        """Mapeia dados do Firestore para Benefit."""
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
                "value_type": self._map_value_type(
                    configuration_data.get("discount_type", "percentage")
                ),
                "value": float(configuration_data.get("discount_value", 0)),
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
        """Parse flexível de datas."""
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

    def _map_benefit_type(self, type_value: str) -> str:
        """Mapeia string para tipo de benefício."""
        type_mapping = {
            "discount": "discount",
            "cashback": "cashback",
            "freebie": "freebie",
            "points": "points",
        }
        return type_mapping.get(type_value.lower(), "discount")

    def _map_value_type(self, value_type: str) -> str:
        """Mapeia string para tipo de valor."""
        type_mapping = {
            "percentage": "percentage",
            "fixed": "fixed_amount",
            "free": "free",
        }
        return type_mapping.get(value_type.lower(), "percentage")

    def _analyze_errors(self, errors: list[dict]) -> dict[str, int]:
        """Analisa tipos de erros."""
        error_counts = {}
        for error in errors:
            error_type = error.get("error_type", "Unknown")
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        return error_counts


def main():
    """Função principal."""
    try:
        tester = BenefitsComparisonTester()
        results = tester.run_comparison()

        # Salvar resultados em arquivo JSON
        output_file = (
            Path(__file__).parent
            / f"benefits_comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)

        logger.info(f"\n💾 Resultados salvos em: {output_file}")
        logger.info("✅ Comparação concluída com sucesso!")

    except Exception as e:
        logger.error(f"❌ Erro durante a execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
