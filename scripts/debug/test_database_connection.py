#!/usr/bin/env python3
"""
Script para testar a conexão com PostgreSQL e diagnosticar problemas.

Este script:
1. Testa a conexão com PostgreSQL usando as configurações do .env
2. Verifica se o banco de dados existe
3. Lista as tabelas disponíveis
4. Testa uma consulta simples

Uso:
    python scripts/debug/test_database_connection.py
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


class DatabaseConnectionTester:
    """Classe para testar a conexão com PostgreSQL."""

    def __init__(self):
        """Inicializar o testador."""
        # Carregar variáveis de ambiente
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        
        self.connection_string = os.getenv(
            "POSTGRES_CONNECTION_STRING", 
            "postgresql://postgres:postgres@localhost:5432/knn_portal"
        )

    def print_step(self, message: str, emoji: str = "🔄") -> None:
        """Imprimir uma etapa do processo."""
        print(f"\n{emoji} {message}")

    def print_success(self, message: str) -> None:
        """Imprimir mensagem de sucesso."""
        print(f"✅ {message}")

    def print_error(self, message: str) -> None:
        """Imprimir mensagem de erro."""
        print(f"❌ {message}")

    def print_info(self, message: str) -> None:
        """Imprimir informação."""
        print(f"ℹ️  {message}")

    def test_basic_connection(self) -> bool:
        """
        Testar conexão básica com PostgreSQL.

        Returns:
            bool: True se a conexão foi bem-sucedida
        """
        self.print_step("Testando conexão básica com PostgreSQL", "🔌")
        
        try:
            self.print_info(f"String de conexão: {self.connection_string}")
            
            # Tentar conectar com encoding específico
            conn = psycopg2.connect(
                self.connection_string,
                client_encoding='utf8'
            )
            cursor = conn.cursor()
            
            # Testar uma consulta simples
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            self.print_success("Conexão com PostgreSQL bem-sucedida!")
            self.print_info(f"Versão do PostgreSQL: {version[0]}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except psycopg2.OperationalError as e:
            self.print_error(f"Erro de conexão: {str(e)}")
            return False
        except Exception as e:
            self.print_error(f"Erro inesperado: {str(e)}")
            return False

    def test_database_exists(self) -> bool:
        """
        Testar se o banco de dados existe.

        Returns:
            bool: True se o banco existe
        """
        self.print_step("Verificando se o banco de dados existe", "🗄️")
        
        try:
            # Conectar ao banco postgres para verificar se knn_portal existe
            base_conn_string = self.connection_string.replace("/knn_portal", "/postgres")
            
            conn = psycopg2.connect(
                base_conn_string,
                client_encoding='utf8'
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Verificar se o banco knn_portal existe
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = 'knn_portal';"
            )
            result = cursor.fetchone()
            
            if result:
                self.print_success("Banco de dados 'knn_portal' existe!")
            else:
                self.print_error("Banco de dados 'knn_portal' não existe!")
                self.print_info("Criando banco de dados...")
                
                # Criar o banco de dados
                cursor.execute("CREATE DATABASE knn_portal;")
                self.print_success("Banco de dados 'knn_portal' criado!")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.print_error(f"Erro ao verificar banco: {str(e)}")
            return False

    def test_tables_exist(self) -> bool:
        """
        Testar se as tabelas necessárias existem.

        Returns:
            bool: True se as tabelas existem
        """
        self.print_step("Verificando tabelas no banco", "📋")
        
        try:
            conn = psycopg2.connect(
                self.connection_string,
                client_encoding='utf8'
            )
            cursor = conn.cursor()
            
            # Listar todas as tabelas
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            
            if tables:
                self.print_success(f"Encontradas {len(tables)} tabelas:")
                for table in tables:
                    self.print_info(f"  - {table[0]}")
            else:
                self.print_error("Nenhuma tabela encontrada no banco!")
                self.print_info("O banco pode estar vazio ou não inicializado.")
            
            # Verificar especificamente a tabela partners
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'partners'
                );
            """)
            
            partners_exists = cursor.fetchone()[0]
            
            if partners_exists:
                self.print_success("Tabela 'partners' existe!")
                
                # Contar registros na tabela partners
                cursor.execute("SELECT COUNT(*) FROM partners;")
                count = cursor.fetchone()[0]
                self.print_info(f"Registros na tabela partners: {count}")
                
            else:
                self.print_error("Tabela 'partners' não existe!")
            
            cursor.close()
            conn.close()
            
            return partners_exists
            
        except Exception as e:
            self.print_error(f"Erro ao verificar tabelas: {str(e)}")
            return False

    def test_connection_pool(self) -> bool:
        """
        Testar múltiplas conexões para simular um pool.

        Returns:
            bool: True se o teste foi bem-sucedido
        """
        self.print_step("Testando múltiplas conexões (simulando pool)", "🏊")
        
        connections = []
        
        try:
            # Criar múltiplas conexões
            for i in range(3):
                conn = psycopg2.connect(
                    self.connection_string,
                    client_encoding='utf8'
                )
                connections.append(conn)
                self.print_info(f"Conexão {i+1} criada com sucesso")
            
            # Testar consultas em cada conexão
            for i, conn in enumerate(connections):
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                cursor.close()
                self.print_info(f"Consulta na conexão {i+1}: {result[0]}")
            
            self.print_success("Múltiplas conexões funcionando!")
            
            return True
            
        except Exception as e:
            self.print_error(f"Erro no teste de múltiplas conexões: {str(e)}")
            return False
            
        finally:
            # Fechar todas as conexões
            for conn in connections:
                try:
                    conn.close()
                except:
                    pass

    def run_tests(self) -> bool:
        """Executar todos os testes de conexão."""
        print("🚀 Testando conexão com PostgreSQL...")
        
        success = True
        
        # Teste 1: Conexão básica
        if not self.test_basic_connection():
            success = False
        
        # Teste 2: Verificar se o banco existe
        if not self.test_database_exists():
            success = False
        
        # Teste 3: Verificar tabelas
        if not self.test_tables_exist():
            success = False
        
        # Teste 4: Pool de conexões
        if not self.test_connection_pool():
            success = False
        
        if success:
            print("\n🎉 Todos os testes de conexão passaram!")
        else:
            print("\n❌ Alguns testes falharam!")
        
        return success


def main():
    """Função principal."""
    try:
        tester = DatabaseConnectionTester()
        success = tester.run_tests()

        if success:
            print("\n✅ Conexão com PostgreSQL está funcionando!")
            sys.exit(0)
        else:
            print("\n❌ Problemas encontrados na conexão com PostgreSQL!")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Erro fatal: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()