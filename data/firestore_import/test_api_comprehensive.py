#!/usr/bin/env python3
"""
Script abrangente para testar endpoints da API com diferentes cenários de autenticação.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from google.cloud import firestore
from google.oauth2 import service_account

# Configurações
BASE_URL = "http://localhost:8080/v1"
PROJECT_ID = "knn-benefits"
DATABASE_ID = "(default)"
SERVICE_ACCOUNT_KEY = "default-service-account-key.json"

# Headers padrão
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

class ComprehensiveAPITester:
    """Classe para testar endpoints da API de forma abrangente."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.firestore_client = None
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def get_firestore_client(self):
        """Inicializa cliente Firestore para obter dados de teste."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_KEY
            )
            
            client = firestore.Client(
                project=PROJECT_ID,
                database=DATABASE_ID,
                credentials=credentials
            )
            
            print(f"✅ Conectado ao Firestore - Projeto: {PROJECT_ID}, Banco: {DATABASE_ID}")
            return client
            
        except Exception as e:
            print(f"❌ Erro ao conectar ao Firestore: {e}")
            return None
    
    async def log_test_result(self, test_name: str, success: bool, details: str = "", expected_status: int = None, actual_status: int = None):
        """Registra resultado de um teste."""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} - {test_name}")
        if details:
            print(f"   Detalhes: {details}")
        if expected_status and actual_status:
            print(f"   Status: esperado {expected_status}, recebido {actual_status}")
    
    async def test_health_check(self):
        """Testa endpoint de health check (não requer autenticação)."""
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    await self.log_test_result(
                        "Health Check", 
                        True, 
                        f"Status: {data.get('status')}, Mode: {data.get('mode')}",
                        200,
                        response.status_code
                    )
                else:
                    await self.log_test_result(
                        "Health Check", 
                        False, 
                        f"Status inesperado: {data}",
                        200,
                        response.status_code
                    )
            else:
                await self.log_test_result(
                    "Health Check", 
                    False, 
                    f"Status code inesperado",
                    200,
                    response.status_code
                )
                
        except Exception as e:
            await self.log_test_result(
                "Health Check", 
                False, 
                f"Erro: {str(e)}"
            )
    
    async def test_authentication_middleware(self):
        """Testa o middleware de autenticação."""
        
        # Teste 1: Requisição sem token (deve retornar 400)
        try:
            response = await self.client.get(f"{BASE_URL}/student/partners")
            
            if response.status_code == 400:
                data = response.json()
                if "Token JWT ausente" in data.get("error", {}).get("msg", ""):
                    await self.log_test_result(
                        "Middleware - Sem Token", 
                        True, 
                        "Corretamente rejeitou requisição sem token JWT",
                        400,
                        response.status_code
                    )
                else:
                    await self.log_test_result(
                        "Middleware - Sem Token", 
                        True, 
                        f"Rejeitou sem token, mas com mensagem diferente: {data}",
                        400,
                        response.status_code
                    )
            else:
                await self.log_test_result(
                    "Middleware - Sem Token", 
                    False, 
                    f"Status inesperado",
                    400,
                    response.status_code
                )
        except Exception as e:
            await self.log_test_result(
                "Middleware - Sem Token", 
                False, 
                f"Erro: {str(e)}"
            )
        
        # Teste 2: Token inválido (deve retornar 400)
        try:
            headers = {**HEADERS, "Authorization": "Bearer token-invalido"}
            response = await self.client.get(f"{BASE_URL}/student/partners", headers=headers)
            
            if response.status_code == 400:
                data = response.json()
                await self.log_test_result(
                    "Middleware - Token Inválido", 
                    True, 
                    f"Corretamente rejeitou token inválido: {data.get('error', {}).get('msg', '')}",
                    400,
                    response.status_code
                )
            else:
                await self.log_test_result(
                    "Middleware - Token Inválido", 
                    False, 
                    f"Status inesperado",
                    400,
                    response.status_code
                )
        except Exception as e:
            await self.log_test_result(
                "Middleware - Token Inválido", 
                False, 
                f"Erro: {str(e)}"
            )
        
        # Teste 3: Token sem tenant (deve retornar 400)
        try:
            # Token JWT básico sem tenant (apenas para teste)
            token_sem_tenant = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            headers = {**HEADERS, "Authorization": f"Bearer {token_sem_tenant}"}
            response = await self.client.get(f"{BASE_URL}/student/partners", headers=headers)
            
            if response.status_code == 400:
                data = response.json()
                if "tenant missing" in data.get("error", {}).get("msg", ""):
                    await self.log_test_result(
                        "Middleware - Token Sem Tenant", 
                        True, 
                        "Corretamente rejeitou token sem tenant",
                        400,
                        response.status_code
                    )
                else:
                    await self.log_test_result(
                        "Middleware - Token Sem Tenant", 
                        True, 
                        f"Rejeitou token, mas com mensagem diferente: {data}",
                        400,
                        response.status_code
                    )
            else:
                await self.log_test_result(
                    "Middleware - Token Sem Tenant", 
                    False, 
                    f"Status inesperado",
                    400,
                    response.status_code
                )
        except Exception as e:
            await self.log_test_result(
                "Middleware - Token Sem Tenant", 
                False, 
                f"Erro: {str(e)}"
            )
    
    async def test_endpoints_structure(self):
        """Testa a estrutura dos endpoints disponíveis."""
        
        # Lista de endpoints para testar (sem autenticação, esperando 400)
        endpoints_to_test = [
            ("/student/partners", "Estudantes - Lista Parceiros"),
            ("/student/students/me/history", "Estudantes - Histórico"),
            ("/student/students/me/fav", "Estudantes - Favoritos"),
            ("/employee/partners", "Funcionários - Lista Parceiros"),
            ("/employee/me", "Funcionários - Perfil"),
            ("/admin/partners", "Admin - Lista Parceiros"),
            ("/admin/metrics", "Admin - Métricas"),
            ("/partner/partner/promotions", "Parceiros - Promoções"),
        ]
        
        for endpoint, test_name in endpoints_to_test:
            try:
                response = await self.client.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 400:
                    await self.log_test_result(
                        f"Endpoint Existe - {test_name}", 
                        True, 
                        "Endpoint existe e rejeita requisições sem autenticação",
                        400,
                        response.status_code
                    )
                elif response.status_code == 404:
                    await self.log_test_result(
                        f"Endpoint Existe - {test_name}", 
                        False, 
                        "Endpoint não encontrado",
                        400,
                        response.status_code
                    )
                else:
                    await self.log_test_result(
                        f"Endpoint Existe - {test_name}", 
                        False, 
                        f"Status inesperado",
                        400,
                        response.status_code
                    )
            except Exception as e:
                await self.log_test_result(
                    f"Endpoint Existe - {test_name}", 
                    False, 
                    f"Erro: {str(e)}"
                )
    
    async def test_invalid_endpoints(self):
        """Testa endpoints inexistentes."""
        invalid_endpoints = [
            "/invalid/endpoint",
            "/student/invalid",
            "/admin/invalid",
            "/nonexistent"
        ]
        
        for endpoint in invalid_endpoints:
            try:
                response = await self.client.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 404:
                    await self.log_test_result(
                        f"Endpoint Inexistente - {endpoint}", 
                        True, 
                        "Corretamente retornou 404 para endpoint inexistente",
                        404,
                        response.status_code
                    )
                else:
                    await self.log_test_result(
                        f"Endpoint Inexistente - {endpoint}", 
                        False, 
                        f"Status inesperado",
                        404,
                        response.status_code
                    )
            except Exception as e:
                await self.log_test_result(
                    f"Endpoint Inexistente - {endpoint}", 
                    False, 
                    f"Erro: {str(e)}"
                )
    
    async def test_database_connectivity(self):
        """Testa conectividade com o banco de dados."""
        if not self.firestore_client:
            self.firestore_client = self.get_firestore_client()
        
        if not self.firestore_client:
            await self.log_test_result(
                "Database - Conectividade", 
                False, 
                "Não foi possível conectar ao Firestore"
            )
            return
        
        try:
            # Testar coleção de estudantes
            students_ref = self.firestore_client.collection('students')
            students_docs = list(students_ref.limit(1).stream())
            
            # Testar coleção de funcionários
            employees_ref = self.firestore_client.collection('employees')
            employees_docs = list(employees_ref.limit(1).stream())
            
            await self.log_test_result(
                "Database - Conectividade", 
                True, 
                f"Conectado ao Firestore. Estudantes: {len(students_docs)}, Funcionários: {len(employees_docs)}"
            )
            
        except Exception as e:
            await self.log_test_result(
                "Database - Conectividade", 
                False, 
                f"Erro ao acessar Firestore: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Executa todos os testes."""
        print("\n=== INICIANDO TESTES ABRANGENTES DA API ===")
        print(f"URL Base: {BASE_URL}")
        print(f"Banco de Dados: {PROJECT_ID}/{DATABASE_ID}")
        print("\n" + "="*60)
        
        # Executar testes
        await self.test_health_check()
        await self.test_database_connectivity()
        await self.test_authentication_middleware()
        await self.test_endpoints_structure()
        await self.test_invalid_endpoints()
        
        # Resumo dos resultados
        print("\n" + "="*60)
        print("=== RESUMO DOS TESTES ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\nTotal de testes: {total_tests}")
        print(f"✅ Testes aprovados: {passed_tests}")
        print(f"❌ Testes falharam: {failed_tests}")
        print(f"📊 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        # Mostrar testes que falharam
        if failed_tests > 0:
            print("\n⚠️  Testes que falharam:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        # Salvar resultados em arquivo
        results_file = "test_api_comprehensive_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100,
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Resultados detalhados salvos em: {results_file}")
        
        if failed_tests == 0:
            print("\n🎉 Todos os testes passaram! A API está funcionando corretamente.")
        else:
            print(f"\n⚠️  {failed_tests} teste(s) falharam. Verifique os detalhes acima.")


async def main():
    """Função principal."""
    async with ComprehensiveAPITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())