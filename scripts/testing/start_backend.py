#!/usr/bin/env python3
"""
Script de inicialização automática do backend para testes.

Este script gerencia a inicialização e parada do servidor backend
FastAPI durante a execução dos testes automatizados.
"""

import logging
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests
from requests.exceptions import RequestException

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BackendManager:
    """Gerenciador do servidor backend para testes."""

    def __init__(
        self,
        backend_host: str = "localhost",
        backend_port: int = 8000,
        startup_timeout: int = 30,
        health_check_interval: float = 1.0,
    ):
        """
        Inicializa o gerenciador do backend.

        Args:
            backend_host: Host do servidor backend
            backend_port: Porta do servidor backend
            startup_timeout: Timeout para inicialização em segundos
            health_check_interval: Intervalo entre verificações de saúde
        """
        self.host = backend_host
        self.port = backend_port
        self.startup_timeout = startup_timeout
        self.health_check_interval = health_check_interval

        self.base_url = f"http://{self.host}:{self.port}"
        self.health_url = f"{self.base_url}/v1/health"

        self.process: subprocess.Popen | None = None
        self.is_running = False
        self.should_stop = False

        # Encontrar diretório raiz do projeto
        self.project_root = self._find_project_root()

        # Configurar manipulador de sinais
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _find_project_root(self) -> Path:
        """Encontra o diretório raiz do projeto."""
        current_dir = Path(__file__).parent.absolute()

        # Procurar por arquivos indicadores do projeto
        indicators = ["requirements.txt", "pyproject.toml"]
        src_indicators = ["src/main.py", "main.py"]

        # Subir até 3 níveis para encontrar a raiz
        for _ in range(3):
            # Verificar se tem os arquivos de configuração E o main.py
            has_config = any((current_dir / indicator).exists() for indicator in indicators)
            has_main = any((current_dir / indicator).exists() for indicator in src_indicators)
            
            if has_config and has_main:
                logger.info(f"Diretório do projeto encontrado: {current_dir}")
                return current_dir

            parent = current_dir.parent
            if parent == current_dir:  # Chegou na raiz do sistema
                break
            current_dir = parent

        # Fallback para diretório atual
        fallback = Path.cwd()
        logger.warning(f"Raiz do projeto não encontrada, usando: {fallback}")
        return fallback

    def _signal_handler(self, signum, frame):
        """Manipula sinais do sistema para parada limpa."""
        logger.info(f"Sinal {signum} recebido, parando servidor...")
        self.should_stop = True
        self.stop_backend()

    def _check_port_available(self) -> bool:
        """Verifica se a porta está disponível."""
        try:
            requests.get(self.health_url, timeout=2)
            # Se conseguiu conectar, a porta está ocupada
            logger.info(f"Servidor já está rodando na porta {self.port}")
            return False
        except RequestException:
            # Não conseguiu conectar, porta disponível
            return True

    def _wait_for_health_check(self) -> bool:
        """Aguarda o servidor ficar disponível via health check."""
        logger.info(f"Aguardando servidor ficar disponível em {self.health_url}")

        start_time = time.time()

        while time.time() - start_time < self.startup_timeout:
            if self.should_stop:
                return False

            try:
                response = requests.get(self.health_url, timeout=2)
                if response.status_code == 200:
                    logger.info("✅ Servidor backend está disponível")
                    return True
                else:
                    logger.debug(f"Health check retornou: {response.status_code}")

            except RequestException as e:
                logger.debug(f"Health check falhou: {e}")

            time.sleep(self.health_check_interval)

        logger.error(f"Timeout aguardando servidor ({self.startup_timeout}s)")
        return False

    def _find_main_file(self) -> Path | None:
        """Encontra o arquivo principal do FastAPI."""
        possible_locations = [
            self.project_root / "main.py",
            self.project_root / "src" / "main.py",
            self.project_root / "app" / "main.py",
            self.project_root / "backend" / "main.py",
        ]

        for location in possible_locations:
            if location.exists():
                logger.info(f"Arquivo principal encontrado: {location}")
                return location

        logger.error("Arquivo main.py não encontrado")
        return None

    def start_backend(self) -> bool:
        """Inicia o servidor backend."""
        if not self._check_port_available():
            # Servidor já está rodando
            self.is_running = True
            return True

        main_file = self._find_main_file()
        if not main_file:
            return False

        logger.info(f"Iniciando servidor backend na porta {self.port}")

        # Comando para iniciar o servidor
        # Determinar o módulo correto baseado na localização do main.py
        if "src" in str(main_file):
            app_module = "src.main:app"
        else:
            app_module = "main:app"
            
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            app_module,
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--reload",
            "--log-level",
            "info",
        ]

        try:
            # Iniciar processo em background
            self.process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            logger.info(f"Processo iniciado com PID: {self.process.pid}")

            # Iniciar thread para monitorar saída
            self._start_output_monitor()

            # Aguardar servidor ficar disponível
            if self._wait_for_health_check():
                self.is_running = True
                logger.info("🚀 Servidor backend iniciado com sucesso")
                return True
            else:
                self.stop_backend()
                return False

        except Exception as e:
            logger.error(f"Erro ao iniciar servidor: {e}")
            return False

    def _start_output_monitor(self):
        """Inicia thread para monitorar saída do processo."""

        def monitor_stdout():
            if self.process and self.process.stdout:
                for line in iter(self.process.stdout.readline, ""):
                    if line.strip():
                        logger.debug(f"STDOUT: {line.strip()}")
                    if self.should_stop:
                        break

        def monitor_stderr():
            if self.process and self.process.stderr:
                for line in iter(self.process.stderr.readline, ""):
                    if line.strip():
                        logger.warning(f"STDERR: {line.strip()}")
                    if self.should_stop:
                        break

        # Iniciar threads de monitoramento
        threading.Thread(target=monitor_stdout, daemon=True).start()
        threading.Thread(target=monitor_stderr, daemon=True).start()

    def stop_backend(self):
        """Para o servidor backend."""
        if not self.process:
            logger.info("Nenhum processo para parar")
            return

        logger.info("Parando servidor backend...")

        try:
            # Tentar parada limpa primeiro
            self.process.terminate()

            # Aguardar até 10 segundos pela parada
            try:
                self.process.wait(timeout=10)
                logger.info("✅ Servidor parado com sucesso")
            except subprocess.TimeoutExpired:
                # Forçar parada se necessário
                logger.warning("Forçando parada do servidor...")
                self.process.kill()
                self.process.wait()
                logger.info("✅ Servidor forçado a parar")

        except Exception as e:
            logger.error(f"Erro ao parar servidor: {e}")
        finally:
            self.process = None
            self.is_running = False

    def restart_backend(self) -> bool:
        """Reinicia o servidor backend."""
        logger.info("Reiniciando servidor backend...")
        self.stop_backend()
        time.sleep(2)  # Aguardar limpeza
        return self.start_backend()

    def is_backend_healthy(self) -> bool:
        """Verifica se o backend está saudável."""
        try:
            response = requests.get(self.health_url, timeout=5)
            return response.status_code == 200
        except RequestException:
            return False

    def wait_for_backend(self, timeout: int = 30) -> bool:
        """Aguarda o backend ficar disponível."""
        if self.is_backend_healthy():
            return True

        if not self.is_running:
            logger.info("Backend não está rodando, iniciando...")
            if not self.start_backend():
                return False

        return self._wait_for_health_check()

    def get_backend_info(self) -> dict:
        """Obtém informações do backend."""
        info = {
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "health_url": self.health_url,
            "is_running": self.is_running,
            "process_id": self.process.pid if self.process else None,
            "project_root": str(self.project_root),
        }

        # Verificar saúde se estiver rodando
        if self.is_running:
            info["is_healthy"] = self.is_backend_healthy()

        return info


def main():
    """Função principal para uso standalone."""
    import argparse

    parser = argparse.ArgumentParser(description="Gerenciador do servidor backend")
    parser.add_argument("--host", default="localhost", help="Host do servidor")
    parser.add_argument("--port", type=int, default=8000, help="Porta do servidor")
    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout de inicialização"
    )
    parser.add_argument(
        "--action",
        choices=["start", "stop", "restart", "status"],
        default="start",
        help="Ação a executar",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Aguardar até o servidor parar (apenas para start)",
    )

    args = parser.parse_args()

    manager = BackendManager(
        backend_host=args.host, backend_port=args.port, startup_timeout=args.timeout
    )

    try:
        if args.action == "start":
            if manager.start_backend():
                print(f"✅ Servidor iniciado em {manager.base_url}")

                if args.wait:
                    print("Pressione Ctrl+C para parar o servidor")
                    try:
                        while manager.is_running and not manager.should_stop:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\n⚠️ Interrompido pelo usuário")
                    finally:
                        manager.stop_backend()

                sys.exit(0)
            else:
                print("❌ Falha ao iniciar servidor")
                sys.exit(1)

        elif args.action == "stop":
            manager.stop_backend()
            print("✅ Servidor parado")

        elif args.action == "restart":
            if manager.restart_backend():
                print(f"✅ Servidor reiniciado em {manager.base_url}")
                sys.exit(0)
            else:
                print("❌ Falha ao reiniciar servidor")
                sys.exit(1)

        elif args.action == "status":
            info = manager.get_backend_info()
            print("📊 Status do Backend:")
            for key, value in info.items():
                print(f"   {key}: {value}")

            if info.get("is_running"):
                health = "✅ Saudável" if info.get("is_healthy") else "❌ Não saudável"
                print(f"   Saúde: {health}")

    except KeyboardInterrupt:
        print("\n⚠️ Operação interrompida")
        manager.stop_backend()
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
