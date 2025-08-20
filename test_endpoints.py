"""
Script para testar os endpoints do Portal de Benefícios KNN localmente.
"""
import asyncio
import json
import httpx
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configurações
BASE_URL = "http://localhost:8080/v1"
STUDENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50LWlkIiwicm9sZSI6InN0dWRlbnQiLCJleHAiOjE3MTY5OTIwMDAsImlhdCI6MTcxNjkwNTYwMH0.8Uj7hl5vYGnEZQGR5QeQQOdTKB4ZXEfEiqxJxlE5Pjw"
PARTNER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJ0bmVyLWlkIiwicm9sZSI6InBhcnRuZXIiLCJleHAiOjE3MTY5OTIwMDAsImlhdCI6MTcxNjkwNTYwMH0.Hn5Fq5qSVBN5QjuoYd2KBjTIGJJoV9OQh-VzpNqJrSs"
EMPLOYEE_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZS1pZCIsInJvbGUiOiJlbXBsb3llZSIsImV4cCI6MTcxNjk5MjAwMCwiaWF0IjoxNzE2OTA1NjAwfQ.Kj8Hn5Fq5qSVBN5QjuoYd2KBjTIGJJoV9OQh-VzpNqJ"
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbi1pZCIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcxNjk5MjAwMCwiaWF0IjoxNzE2OTA1NjAwfQ.jQyOq0-KnzH0vqBQwKsqzTBGzKqGLYVj9WdAZKbK5Hs"

# Função para fazer requisições HTTP
async def make_request(
    method: str,
    endpoint: str,
    token: str = None,
    data: Dict[str, Any] = None,
    params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Faz uma requisição HTTP para o endpoint especificado.
    
    Args:
        method: Método HTTP (GET, POST, PUT, DELETE)
        endpoint: Endpoint da API
        token: Token JWT (opcional)
        data: Dados para enviar no corpo da requisição (opcional)
        params: Parâmetros de query string (opcional)
    
    Returns:
        Dict: Resposta da API
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data, params=params)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=data, params=params)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers, params=params)
        else:
            raise ValueError(f"Método HTTP inválido: {method}")
    
    # Imprimir informações da resposta
    print(f"\n{method} {endpoint}")
    print(f"Status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
        return response_data
    except Exception as e:
        print(f"Erro ao processar resposta: {str(e)}")
        print(f"Response text: {response.text}")
        return {"error": str(e)}

# Testes de Health Check
async def test_health_check():
    """Testa o endpoint de health check."""
    print("\n=== TESTE DE HEALTH CHECK ===")
    await make_request("GET", "/health")

# Testes de Autenticação
async def test_authentication():
    """Testa autenticação e autorização."""
    print("\n=== TESTES DE AUTENTICAÇÃO ===")
    
    # Sem token
    await make_request("GET", "/partners")
    
    # Token inválido
    await make_request("GET", "/partners", token="invalid-token")
    
    # Role incorreta
    await make_request("GET", "/partners", token=PARTNER_TOKEN)
    
    # Token correto
    await make_request("GET", "/partners", token=STUDENT_TOKEN)

# Testes de Endpoints para Alunos
async def test_student_endpoints():
    """Testa endpoints para alunos."""
    print("\n=== TESTES DE ENDPOINTS PARA ALUNOS ===")
    
    # Listar parceiros
    partners_response = await make_request("GET", "/partners", token=STUDENT_TOKEN)
    
    # Obter detalhes de um parceiro
    if "data" in partners_response and "items" in partners_response["data"] and partners_response["data"]["items"]:
        partner_id = partners_response["data"]["items"][0]["id"]
        await make_request("GET", f"/partners/{partner_id}", token=STUDENT_TOKEN)
    else:
        print("Não foi possível obter ID de parceiro para teste de detalhes")
    
    # Gerar código de validação
    if "data" in partners_response and "items" in partners_response["data"] and partners_response["data"]["items"]:
        partner_id = partners_response["data"]["items"][0]["id"]
        await make_request("POST", "/validation-codes", token=STUDENT_TOKEN, data={"partner_id": partner_id})
    else:
        print("Não foi possível obter ID de parceiro para teste de geração de código")
    
    # Obter histórico de resgates
    await make_request("GET", "/students/me/history", token=STUDENT_TOKEN)
    
    # Obter favoritos
    await make_request("GET", "/students/me/fav", token=STUDENT_TOKEN)
    
    # Adicionar favorito
    if "data" in partners_response and "items" in partners_response["data"] and partners_response["data"]["items"]:
        partner_id = partners_response["data"]["items"][0]["id"]
        await make_request("POST", "/students/me/fav", token=STUDENT_TOKEN, data={"partner_id": partner_id})
    else:
        print("Não foi possível obter ID de parceiro para teste de adição de favorito")
    
    # Remover favorito
    if "data" in partners_response and "items" in partners_response["data"] and partners_response["data"]["items"]:
        partner_id = partners_response["data"]["items"][0]["id"]
        await make_request("DELETE", f"/students/me/fav/{partner_id}", token=STUDENT_TOKEN)
    else:
        print("Não foi possível obter ID de parceiro para teste de remoção de favorito")

# Testes de Endpoints para Parceiros
async def test_partner_endpoints():
    """Testa endpoints para parceiros."""
    print("\n=== TESTES DE ENDPOINTS PARA PARCEIROS ===")
    
    # Resgatar código (simulação)
    await make_request("POST", "/partner/redeem", token=PARTNER_TOKEN, data={"code": "123456", "cpf": "12345678909"})
    
    # Listar promoções
    promotions_response = await make_request("GET", "/partner/promotions", token=PARTNER_TOKEN)
    
    # Criar promoção
    promotion_data = {
        "title": "Promoção de Teste",
        "type": "discount",
        "valid_from": (datetime.now() - timedelta(days=1)).isoformat(),
        "valid_to": (datetime.now() + timedelta(days=30)).isoformat(),
        "active": True
    }
    promotion_response = await make_request("POST", "/partner/promotions", token=PARTNER_TOKEN, data=promotion_data)
    
    # Atualizar promoção
    if "data" in promotion_response and "id" in promotion_response["data"]:
        promotion_id = promotion_response["data"]["id"]
        promotion_data["title"] = "Promoção de Teste Atualizada"
        await make_request("PUT", f"/partner/promotions/{promotion_id}", token=PARTNER_TOKEN, data=promotion_data)
    else:
        print("Não foi possível obter ID de promoção para teste de atualização")
    
    # Desativar promoção
    if "data" in promotion_response and "id" in promotion_response["data"]:
        promotion_id = promotion_response["data"]["id"]
        await make_request("DELETE", f"/partner/promotions/{promotion_id}", token=PARTNER_TOKEN)
    else:
        print("Não foi possível obter ID de promoção para teste de desativação")
    
    # Obter relatório
    await make_request("GET", "/partner/reports", token=PARTNER_TOKEN, params={"range": "2025-05"})

# Testes de Endpoints para Funcionários
async def test_employee_endpoints():
    """Testa endpoints para funcionários."""
    print("\n=== TESTES DE ENDPOINTS PARA FUNCIONÁRIOS ===")
    
    # Listar parceiros
    partners_response = await make_request("GET", "/employees/partners", token=EMPLOYEE_TOKEN)
    
    # Obter detalhes de um parceiro
    if "data" in partners_response and "items" in partners_response["data"] and partners_response["data"]["items"]:
        partner_id = partners_response["data"]["items"][0]["id"]
        await make_request("GET", f"/employees/partners/{partner_id}", token=EMPLOYEE_TOKEN)
    else:
        print("Não foi possível obter ID de parceiro para teste de detalhes")
    
    # Gerar código de validação
    if "data" in partners_response and "items" in partners_response["data"] and partners_response["data"]["items"]:
        partner_id = partners_response["data"]["items"][0]["id"]
        await make_request("POST", "/employees/validation-codes", token=EMPLOYEE_TOKEN, data={"partner_id": partner_id})
    else:
        print("Não foi possível obter ID de parceiro para teste de geração de código")
    
    # Obter histórico de resgates
    await make_request("GET", "/employees/me/history", token=EMPLOYEE_TOKEN)
    
    # Obter favoritos
    await make_request("GET", "/employees/me/fav", token=EMPLOYEE_TOKEN)
    
    # Adicionar favorito
    if "data" in partners_response and "items" in partners_response["data"] and partners_response["data"]["items"]:
        partner_id = partners_response["data"]["items"][0]["id"]
        await make_request("POST", "/employees/me/fav", token=EMPLOYEE_TOKEN, data={"partner_id": partner_id})
    else:
        print("Não foi possível obter ID de parceiro para teste de adição de favorito")
    
    # Remover favorito
    if "data" in partners_response and "items" in partners_response["data"] and partners_response["data"]["items"]:
        partner_id = partners_response["data"]["items"][0]["id"]
        await make_request("DELETE", f"/employees/me/fav/{partner_id}", token=EMPLOYEE_TOKEN)
    else:
        print("Não foi possível obter ID de parceiro para teste de remoção de favorito")

# Testes de Endpoints para Administradores
async def test_admin_endpoints():
    """Testa endpoints para administradores."""
    print("\n=== TESTES DE ENDPOINTS PARA ADMINISTRADORES ===")
    
    # Listar entidades
    for entity in ["students", "partners", "promotions"]:
        await make_request("GET", f"/admin/{entity}", token=ADMIN_TOKEN)
    
    # Criar entidade (exemplo com partner)
    partner_data = {
        "trade_name": "Parceiro de Teste",
        "category": "Teste",
        "address": "Endereço de Teste",
        "active": True
    }
    partner_response = await make_request("POST", "/admin/partners", token=ADMIN_TOKEN, data=partner_data)
    
    # Atualizar entidade
    if "data" in partner_response and "id" in partner_response["data"]:
        partner_id = partner_response["data"]["id"]
        partner_data["trade_name"] = "Parceiro de Teste Atualizado"
        await make_request("PUT", f"/admin/partners/{partner_id}", token=ADMIN_TOKEN, data=partner_data)
    else:
        print("Não foi possível obter ID de parceiro para teste de atualização")
    
    # Remover entidade
    if "data" in partner_response and "id" in partner_response["data"]:
        partner_id = partner_response["data"]["id"]
        await make_request("DELETE", f"/admin/partners/{partner_id}", token=ADMIN_TOKEN)
    else:
        print("Não foi possível obter ID de parceiro para teste de remoção")
    
    # Obter métricas
    await make_request("GET", "/admin/metrics", token=ADMIN_TOKEN)
    
    # Enviar notificações
    notification_data = {
        "target": "students",
        "filter": {},
        "message": "Mensagem de teste",
        "type": "both"
    }
    await make_request("POST", "/admin/notifications", token=ADMIN_TOKEN, data=notification_data)

# Testes de Rate Limit
async def test_rate_limit():
    """Testa rate limit no endpoint de resgate."""
    print("\n=== TESTE DE RATE LIMIT ===")
    
    # Fazer 6 requisições (o limite é 5 por minuto)
    for i in range(6):
        print(f"\nRequisição {i+1}/6")
        await make_request("POST", "/partner/redeem", token=PARTNER_TOKEN, data={"code": "123456", "cpf": "12345678909"})
        if i < 5:
            time.sleep(1)  # Pequeno delay entre requisições

# Função principal
async def main():
    """Função principal para executar todos os testes."""
    print("=== INICIANDO TESTES DO PORTAL DE BENEFÍCIOS KNN ===")
    
    # Testar health check
    await test_health_check()
    
    # Testar autenticação
    await test_authentication()
    
    # Testar endpoints para alunos
    await test_student_endpoints()
    
    # Testar endpoints para parceiros
    await test_partner_endpoints()
    
    # Testar endpoints para funcionários
    await test_employee_endpoints()
    
    # Testar endpoints para administradores
    await test_admin_endpoints()
    
    # Testar rate limit
    await test_rate_limit()
    
    print("\n=== TESTES CONCLUÍDOS ===")

if __name__ == "__main__":
    asyncio.run(main())
