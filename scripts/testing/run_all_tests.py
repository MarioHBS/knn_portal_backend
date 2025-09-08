#!/usr/bin/env python3
"""
Script principal para execução completa de testes de endpoints.

Este script orquestra todo o processo de testes:
1. Inicializa o backend FastAPI
2. Executa todos os testes de endpoints
3. Gera relatórios detalhados
4. Limpa recursos
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Adicionar diretório de scripts ao path
sys.path.append(str(Path(__file__).parent))

from report_generator import ReportGenerator
from start_backend import BackendManager
from test_admin_endpoints import AdminEndpointTester
from test_config import validate_config
from test_employee_endpoints import EmployeeEndpointTester
from test_partner_endpoints import PartnerEndpointTester
from test_runner import TestRunner
from test_student_endpoints import StudentEndpointTester

logger = logging.getLogger(__name__)


class TestSuiteRunner:
    """Executor principal da suíte de testes."""

    def __init__(self, config_path: str | None = None):
        self.backend_manager = BackendManager()
        self.test_runner = TestRunner()
        self.report_generator = ReportGenerator()

        # Testers específicos
        self.testers = {
            "student": StudentEndpointTester(),
            "employee": EmployeeEndpointTester(),
            "admin": AdminEndpointTester(),
            "partner": PartnerEndpointTester(),
        }

        self.backend_started = False
        self.results = []

    async def setup(self) -> bool:
        """Configura ambiente de testes."""
        try:
            logger.info("🔧 Configurando ambiente de testes...")

            # Validar configuração
            if not validate_config():
                logger.error("❌ Configuração inválida")
                return False

            # Inicializar backend
            logger.info("🚀 Iniciando backend...")
            if not self.backend_manager.start_backend():
                logger.error("❌ Falha ao iniciar backend")
                return False

            self.backend_started = True

            # Aguardar backend estar pronto
            logger.info("⏳ Aguardando backend estar pronto...")
            if not self.backend_manager.wait_for_backend(timeout=30):
                logger.error("❌ Backend não respondeu no tempo esperado")
                return False

            logger.info("✅ Ambiente configurado com sucesso")
            return True

        except Exception as e:
            logger.error(f"❌ Erro na configuração: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """Executa todos os testes."""
        try:
            logger.info("🧪 Iniciando execução de testes...")

            all_results = []

            # Executar testes por perfil
            for profile_name, tester in self.testers.items():
                logger.info(
                    f"\n👤 Executando testes para perfil: {profile_name.upper()}"
                )

                try:
                    profile_results = await tester.run_all_tests()
                    all_results.extend(profile_results)

                    # Log resumo do perfil
                    passed = len([r for r in profile_results if r.status == "pass"])
                    failed = len([r for r in profile_results if r.status == "fail"])
                    skipped = len([r for r in profile_results if r.status == "skip"])

                    logger.info(
                        f"   📊 {profile_name}: {len(profile_results)} testes | "
                        f"✅ {passed} | ❌ {failed} | ⏭️ {skipped}"
                    )

                except Exception as e:
                    logger.error(f"❌ Erro nos testes do perfil {profile_name}: {e}")
                    continue

            self.results = all_results

            # Log resumo geral
            total_tests = len(all_results)
            total_passed = len([r for r in all_results if r.status == "pass"])
            total_failed = len([r for r in all_results if r.status == "fail"])
            total_skipped = len([r for r in all_results if r.status == "skip"])

            success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

            logger.info("\n📊 RESUMO GERAL DOS TESTES")
            logger.info(f"   Total: {total_tests}")
            logger.info(f"   ✅ Aprovados: {total_passed}")
            logger.info(f"   ❌ Falharam: {total_failed}")
            logger.info(f"   ⏭️ Ignorados: {total_skipped}")
            logger.info(f"   📈 Taxa de sucesso: {success_rate:.1f}%")

            return total_failed == 0

        except Exception as e:
            logger.error(f"❌ Erro na execução dos testes: {e}")
            return False

    async def generate_reports(self) -> dict[str, Path]:
        """Gera relatórios dos testes."""
        try:
            logger.info("📄 Gerando relatórios...")

            if not self.results:
                logger.warning("⚠️ Nenhum resultado para gerar relatórios")
                return {}

            reports = self.report_generator.generate_all_reports(self.results)

            logger.info("✅ Relatórios gerados:")
            for format_type, path in reports.items():
                logger.info(f"   📄 {format_type.upper()}: {path}")

            return reports

        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatórios: {e}")
            return {}

    async def cleanup(self):
        """Limpa recursos utilizados."""
        try:
            logger.info("🧹 Limpando recursos...")

            # Parar backend se foi iniciado
            if self.backend_started:
                self.backend_manager.stop_backend()

            # Limpar testers
            for tester in self.testers.values():
                if hasattr(tester, "cleanup"):
                    await tester.cleanup()

            logger.info("✅ Recursos limpos")

        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")

    async def run_complete_suite(self) -> bool:
        """Executa suíte completa de testes."""
        start_time = time.time()
        success = False

        try:
            logger.info("🎯 INICIANDO SUÍTE COMPLETA DE TESTES")
            logger.info("=" * 60)

            # Setup
            if not await self.setup():
                return False

            # Executar testes
            success = await self.run_all_tests()

            # Gerar relatórios
            reports = await self.generate_reports()

            # Estatísticas finais
            end_time = time.time()
            duration = end_time - start_time

            logger.info("\n" + "=" * 60)
            logger.info("🏁 SUÍTE DE TESTES CONCLUÍDA")
            logger.info(f"⏱️ Tempo total: {duration:.2f}s")
            logger.info(
                f"📊 Status: {'✅ SUCESSO' if success else '❌ FALHAS DETECTADAS'}"
            )

            if reports:
                logger.info("📄 Relatórios disponíveis:")
                for format_type, path in reports.items():
                    logger.info(f"   {format_type.upper()}: {path}")

            return success

        except KeyboardInterrupt:
            logger.info("\n⏹️ Execução interrompida pelo usuário")
            return False

        except Exception as e:
            logger.error(f"❌ Erro crítico na suíte de testes: {e}")
            return False

        finally:
            await self.cleanup()


class TestSuiteConfig:
    """Configurações da suíte de testes."""

    def __init__(self):
        self.profiles_to_test = ["student", "employee", "admin", "partner"]
        self.generate_reports = True
        self.report_formats = ["json", "html", "txt"]
        self.stop_on_first_failure = False
        self.parallel_execution = False
        self.timeout_per_test = 30
        self.max_retries = 1
        self.verbose_logging = True


def setup_logging(verbose: bool = True):
    """Configura sistema de logging."""
    level = logging.INFO if verbose else logging.WARNING

    # Configurar formato
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Handler para arquivo
    log_file = Path("reports") / "test_execution.log"
    log_file.parent.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Silenciar logs muito verbosos
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


async def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Executor de testes completo para Portal KNN"
    )
    parser.add_argument(
        "--profiles",
        nargs="+",
        choices=["student", "employee", "admin", "partner"],
        default=["student", "employee", "admin", "partner"],
        help="Perfis a serem testados",
    )
    parser.add_argument(
        "--no-reports", action="store_true", help="Não gerar relatórios"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Modo silencioso (menos logs)"
    )
    parser.add_argument(
        "--stop-on-failure", action="store_true", help="Parar na primeira falha"
    )

    args = parser.parse_args()

    # Configurar logging
    setup_logging(verbose=not args.quiet)

    # Criar e executar suíte
    suite = TestSuiteRunner()

    # Configurar perfis a testar
    if args.profiles:
        suite.testers = {
            profile: suite.testers[profile]
            for profile in args.profiles
            if profile in suite.testers
        }

    try:
        success = await suite.run_complete_suite()

        if success:
            logger.info("\n🎉 Todos os testes passaram!")
            sys.exit(0)
        else:
            logger.error("\n💥 Alguns testes falharam!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        sys.exit(1)


def run_sync():
    """Wrapper síncrono para execução."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Execução interrompida")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_sync()
