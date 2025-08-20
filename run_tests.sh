#!/bin/bash
# Script para executar testes locais do Portal de Benefícios KNN

# Configurar ambiente de teste
export KNN_TEST_MODE=true

# Executar linting com Ruff
echo "Executando linting com Ruff..."
ruff check src/
ruff format --check src/

# Gerar dados de teste
echo "Gerando dados de teste..."
python3 generate_test_data.py

# Executar testes automatizados
echo -e "\n=== Executando testes automatizados ==="
python3 test_endpoints.py

# Instruções para testes manuais
echo -e "\n=== Instruções para testes manuais ==="
echo "1. Execute o servidor FastAPI em um terminal separado:"
echo "   KNN_TEST_MODE=true python3 run_server.py"
echo ""
echo "2. Acesse a documentação Swagger:"
echo "   http://localhost:8080/v1/docs"
echo ""
echo "3. Siga as instruções em manual_tests.md para testes manuais"
echo ""
echo "4. Para simular falhas no Firestore e testar o circuit breaker:"
echo "   - Modifique src/db/mock_db.py e altere FIRESTORE_FAILURE_MODE para True"
echo "   - Reinicie o servidor e observe o comportamento de fallback"
