#!/usr/bin/env python3
"""
Script para testar endpoints da API com dados do banco (default).
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

class APITester:
    """Classe para testar endpoints da API."""
    
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
    
    async def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Registra resultado de um teste."""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} - {test_name}")
        if details:
            print(f"   Detalhes: {details}")
    
    async def test_health_check(self):
        """Testa endpoint de health check."""
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    await self.log_test_result(
                        "Health Check", 
                        True, 
                        f"Status: {data.get('status')}, Mode: {data.get('mode')}"
                    )
                else:
                    await self.log_test_result(
                        "Health Check", 
                        False, 
                        f"Status inesperado: {data}"
                    )
            else:
                await self.log_test_result(
                    "Health Check", 
                    False, 
                    f"Status code: {response.status_code}"
                )
                
        except Exception as e:
            await self.log_test_result(
                "Health Check", 
                False, 
                f"Erro: {str(e)}"
            )
    
    async def test_students_endpoints(self):
        """Testa endpoints relacionados a estudantes."""
        # Obter dados de estudantes do Firestore
        if not self.firestore_client:
            self.firestore_client = self.get_firestore_client()
        
        if not self.firestore_client:
            await self.log_test_result(
                "Estudantes - Preparação", 
                False, 
                "Não foi possível conectar ao Firestore"
            )
            return
        
        try:
            # Obter alguns estudantes para teste
            students_ref = self.firestore_client.collection('students')
            students_docs = students_ref.limit(3).stream()
            students_data = []
            
            for doc in students_docs:
                student_data = doc.to_dict()
                student_data['id'] = doc.id
                students_data.append(student_data)
            
            if not students_data:
                await self.log_test_result(
                    "Estudantes - Preparação", 
                    False, 
                    "Nenhum estudante encontrado no banco"
                )
                return
            
            await self.log_test_result(
                "Estudantes - Preparação", 
                True, 
                f"Encontrados {len(students_data)} estudantes para teste"
            )
            
            # Teste 1: Listar parceiros como estudante (sem autenticação - deve falhar)
            try:
                response = await self.client.get(f"{BASE_URL}/student/partners")
                
                if response.status_code == 401:
                    await self.log_test_result(
                        "Estudantes - Lista Parceiros (sem auth)", 
                        True, 
                        "Corretamente rejeitou requisição sem autenticação"
                    )
                else:
                    await self.log_test_result(
                        "Estudantes - Lista Parceiros (sem auth)", 
                        False, 
                        f"Status inesperado: {response.status_code}"
                    )
            except Exception as e:
                await self.log_test_result(
                    "Estudantes - Lista Parceiros (sem auth)", 
                    False, 
                    f"Erro: {str(e)}"
                )
            
            # Teste 2: Histórico do estudante (sem autenticação)
            try:
                response = await self.client.get(f"{BASE_URL}/student/students/me/history")
                
                if response.status_code == 401:
                    await self.log_test_result(
                        "Estudantes - Histórico (sem auth)", 
                        True, 
                        "Corretamente rejeitou requisição sem autenticação"
                    )
                else:
                    await self.log_test_result(
                        "Estudantes - Histórico (sem auth)", 
                        False, 
                        f"Status inesperado: {response.status_code}"
                    )
            except Exception as e:
                await self.log_test_result(
                    "Estudantes - Histórico (sem auth)", 
                    False, 
                    f"Erro: {str(e)}"
                )
                    
        except Exception as e:
            await self.log_test_result(
                "Estudantes - Preparação", 
                False, 
                f"Erro ao acessar Firestore: {str(e)}"
            )
    
    async def test_employees_endpoints(self):
        """Testa endpoints relacionados a funcionários."""
        if not self.firestore_client:
            self.firestore_client = self.get_firestore_client()
        
        if not self.firestore_client:
            await self.log_test_result(
                "Funcionários - Preparação", 
                False, 
                "Não foi possível conectar ao Firestore"
            )
            return
        
        try:
            # Obter alguns funcionários para teste
            employees_ref = self.firestore_client.collection('employees')
            employees_docs = employees_ref.limit(3).stream()
            employees_data = []
            
            for doc in employees_docs:
                employee_data = doc.to_dict()
                employee_data['id'] = doc.id
                employees_data.append(employee_data)
            
            if not employees_data:
                await self.log_test_result(
                    "Funcionários - Preparação", 
                    False, 
                    "Nenhum funcionário encontrado no banco"
                )
                return
            
            await self.log_test_result(
                "Funcionários - Preparação", 
                True, 
                f"Encontrados {len(employees_data)} funcionários para teste"
            )
            
            # Teste: Endpoints de funcionários (sem autenticação)
            try:
                response = await self.client.get(f"{BASE_URL}/employee/me")
                
                if response.status_code == 401:
                    await self.log_test_result(
                        "Funcionários - Perfil (sem auth)", 
                        True, 
                        "Corretamente rejeitou requisição sem autenticação"
                    )
                else:
                    await self.log_test_result(
                        "Funcionários - Perfil (sem auth)", 
                        False, 
                        f"Status inesperado: {response.status_code}"
                    )
            except Exception as e:
                await self.log_test_result(
                    "Funcionários - Perfil (sem auth)", 
                    False, 
                    f"Erro: {str(e)}"
                )
                
        except Exception as e:
            await self.log_test_result(
                "Funcionários - Preparação", 
                False, 
                f"Erro ao acessar Firestore: {str(e)}"
            )
    
    async def test_admin_endpoints(self):
        """Testa endpoints administrativos."""
        # Teste: Endpoints administrativos (sem autenticação)
        try:
            response = await self.client.get(f"{BASE_URL}/admin/metrics")
            
            if response.status_code == 401:
                await self.log_test_result(
                    "Admin - Métricas (sem auth)", 
                    True, 
                    "Corretamente rejeitou requisição sem autenticação"
                )
            else:
                await self.log_test_result(
                    "Admin - Métricas (sem auth)", 
                    False, 
                    f"Status inesperado: {response.status_code}"
                )
        except Exception as e:
            await self.log_test_result(
                "Admin - Métricas (sem auth)", 
                False, 
                f"Erro: {str(e)}"
            )
    
    async def test_partner_endpoints(self):
        """Testa endpoints relacionados a parceiros."""
        # Teste: Promoções do parceiro (sem autenticação)
        try:
            response = await self.client.get(f"{BASE_URL}/partner/partner/promotions")
            
            if response.status_code == 401:
                await self.log_test_result(
                    "Parceiros - Promoções (sem auth)", 
                    True, 
                    "Corretamente rejeitou requisição sem autenticação"
                )
            else:
                await self.log_test_result(
                    "Parceiros - Promoções (sem auth)", 
                    False, 
                    f"Status inesperado: {response.status_code}"
                )
        except Exception as e:
            await self.log_test_result(
                "Parceiros - Promoções (sem auth)", 
                False, 
                f"Erro: {str(e)}"
            )
    
    async def test_invalid_endpoints(self):
        """Testa endpoints inválidos."""
        # Teste: Endpoint inexistente
        try:
            response = await self.client.get(f"{BASE_URL}/invalid/endpoint")
            
            if response.status_code == 404:
                await self.log_test_result(
                    "Endpoint Inexistente", 
                    True, 
                    "Corretamente retornou 404 para endpoint inexistente"
                )
            else:
                await self.log_test_result(
                    "Endpoint Inexistente", 
                    False, 
                    f"Status inesperado: {response.status_code}"
                )
        except Exception as e:
            await self.log_test_result(
                "Endpoint Inexistente", 
                False, 
                f"Erro: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Executa todos os testes."""
        print("\n=== INICIANDO TESTES DOS ENDPOINTS DA API ===")
        print(f"URL Base: {BASE_URL}")
        print(f"Banco de Dados: {PROJECT_ID}/{DATABASE_ID}")
        print("\n" + "="*50)
        
        # Executar testes
        await self.test_health_check()
        await self.test_students_endpoints()
        await self.test_employees_endpoints()
        await self.test_admin_endpoints()
        await self.test_partner_endpoints()
        await self.test_invalid_endpoints()
        
        # Resumo dos resultados
        print("\n" + "="*50)
        print("=== RESUMO DOS TESTES ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\nTotal de testes: {total_tests}")
        print(f"✅ Testes aprovados: {passed_tests}")
        print(f"❌ Testes falharam: {failed_tests}")
        print(f"📊 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        # Salvar resultados em arquivo
        results_file = "test_api_results.json"
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
        
        print(f"\n📄 Resultados salvos em: {results_file}")
        
        if failed_tests > 0:
            print("\n⚠️  Alguns testes falharam. Verifique os detalhes acima.")
        else:
            print("\n🎉 Todos os testes passaram!")


async def main():
    """Função principal."""
    async with APITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())