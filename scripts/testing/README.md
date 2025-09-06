# 🧪 Suíte de Testes - Portal de Benefícios KNN

Esta documentação descreve a configuração completa de testes para os endpoints da API do Portal de Benefícios KNN.

## 🎯 Visão Geral

A suíte de testes foi desenvolvida para:

- ✅ **Testar todos os endpoints** da API por perfil de usuário
- 🚀 **Inicializar automaticamente** o backend FastAPI
- 📊 **Gerar relatórios detalhados** em múltiplos formatos
- 🔧 **Configuração centralizada** e flexível
- 📈 **Métricas de performance** e cobertura

### Perfis Testados

- 👨‍🎓 **Student**: Endpoints para estudantes
- 👨‍💼 **Employee**: Endpoints para funcionários
- 👨‍💻 **Admin**: Endpoints para administradores
- 🏢 **Partner**: Endpoints para parceiros

## 📁 Estrutura do Projeto

```text
scripts/testing/
├── 📄 README.md                    # Esta documentação
├── ⚙️ test_config.py              # Configurações centralizadas
├── 🎯 test_runner.py               # Executor principal de testes
├── 📊 report_generator.py          # Gerador de relatórios
├── 🚀 start_backend.py             # Gerenciador do backend
├── 🎮 run_all_tests.py             # Script principal
├── 👨‍🎓 test_student_endpoints.py   # Testes de Student
├── 👨‍💼 test_employee_endpoints.py  # Testes de Employee
├── 👨‍💻 test_admin_endpoints.py     # Testes de Admin
└── 🏢 test_partner_endpoints.py    # Testes de Partner

reports/                           # Relatórios gerados
├── 📄 test_report_YYYYMMDD_HHMMSS.html
├── 📄 test_report_YYYYMMDD_HHMMSS.json
├── 📄 test_report_YYYYMMDD_HHMMSS.txt
└── 📄 test_execution.log
```

## 🛠️ Instalação e Configuração

### Pré-requisitos

- Python 3.8+
- FastAPI backend configurado
- Dependências instaladas:

```bash
pip install requests aiohttp fastapi uvicorn
```

### Configuração Inicial

1. **Configure os tokens de autenticação** em `test_config.py`:

```python
AUTH_TOKENS = {
    "student": "seu_token_student_aqui",
    "employee": "seu_token_employee_aqui",
    "admin": "seu_token_admin_aqui",
    "partner": "seu_token_partner_aqui"
}
```

2. **Ajuste as URLs base** se necessário:

```python
BASE_URLS = {
    "student": "http://localhost:8000/student",
    "employee": "http://localhost:8000/employee",
    "admin": "http://localhost:8000/admin",
    "partner": "http://localhost:8000/partner",
    "utils": "http://localhost:8000"
}
```

3. **Valide a configuração**:

```bash
cd scripts/testing
python test_config.py
```

## 🚀 Execução dos Testes

### Execução Completa

Para executar todos os testes com relatórios:

```bash
cd scripts/testing
python run_all_tests.py
```

### Opções de Execução

```bash
# Testar apenas perfis específicos
python run_all_tests.py --profiles student employee

# Modo silencioso
python run_all_tests.py --quiet

# Parar na primeira falha
python run_all_tests.py --stop-on-failure

# Não gerar relatórios
python run_all_tests.py --no-reports
```

### Execução Individual por Perfil

```bash
# Testes de Student
python test_student_endpoints.py

# Testes de Employee
python test_employee_endpoints.py

# Testes de Admin
python test_admin_endpoints.py

# Testes de Partner
python test_partner_endpoints.py
```

### Gerenciamento Manual do Backend

```bash
# Iniciar backend
python start_backend.py start

# Parar backend
python start_backend.py stop

# Reiniciar backend
python start_backend.py restart

# Verificar status
python start_backend.py status
```

## 📊 Relatórios

### Formatos Disponíveis

#### 📄 HTML (Interativo)

- Gráficos interativos
- Tabelas filtráveis
- Design responsivo
- Métricas visuais

#### 📄 JSON (Programático)

- Dados estruturados
- Integração com outras ferramentas
- Análise automatizada

#### 📄 TXT (Simples)

- Leitura rápida
- Logs de execução
- Resumos textuais

### Métricas Incluídas

- 📈 **Taxa de sucesso** por perfil
- ⏱️ **Tempos de resposta** (médio, mínimo, máximo)
- 🎯 **Cobertura de endpoints**
- 📊 **Estatísticas detalhadas**
- 🔍 **Resultados individuais**

### Localização dos Relatórios

Todos os relatórios são salvos na pasta `reports/` com timestamp:

```text
reports/
├── test_report_20240115_143022.html
├── test_report_20240115_143022.json
├── test_report_20240115_143022.txt
└── test_execution.log
```

## ⚙️ Configuração Avançada

### Personalização de Testes

Edite `test_config.py` para:

- Adicionar novos endpoints
- Modificar dados de teste
- Ajustar timeouts
- Configurar retry logic

### Exemplo de Novo Endpoint

```python
ENDPOINTS = {
    "student": {
        # Endpoints existentes...
        "new_endpoint": {
            "method": "POST",
            "path": "/new-feature",
            "test_data": {"param": "value"},
            "expected_status": 201
        }
    }
}
```

### Configuração de Logging

Ajuste o nível de logging em `run_all_tests.py`:

```python
# Mais verboso
logging.basicConfig(level=logging.DEBUG)

# Menos verboso
logging.basicConfig(level=logging.WARNING)
```

## 🔧 Troubleshooting

### Problemas Comuns

#### ❌ Backend não inicia

```bash
# Verificar se a porta está em uso
netstat -ano | findstr :8000

# Matar processo se necessário
taskkill /PID <PID> /F
```

#### ❌ Tokens inválidos

1. Verifique os tokens em `test_config.py`
2. Gere novos tokens se necessário
3. Teste manualmente com curl:

```bash
curl -H "Authorization: Bearer SEU_TOKEN" http://localhost:8000/student/partners
```

#### ❌ Timeouts

1. Aumente o timeout em `test_config.py`:

```python
REQUEST_TIMEOUT = 60  # segundos
```

2. Verifique a performance do backend

#### ❌ Dependências faltando

```bash
pip install -r requirements.txt
```

### Logs de Debug

Para debug detalhado:

```bash
python run_all_tests.py --verbose
```

Ou verifique o log de execução:

```bash
tail -f reports/test_execution.log
```

### Validação de Configuração

```bash
# Testar configuração
python test_config.py

# Testar conectividade
python -c "import requests; print(requests.get('http://localhost:8000/health').status_code)"
```

## 📚 Exemplos de Uso

### Integração com CI/CD

```yaml
# .github/workflows/tests.yml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: |
          cd scripts/testing
          python run_all_tests.py --no-reports
```

### Script de Monitoramento

```bash
#!/bin/bash
# monitor_api.sh

while true; do
    echo "$(date): Executando testes..."
    cd scripts/testing
    python run_all_tests.py --quiet

    if [ $? -eq 0 ]; then
        echo "✅ Testes passaram"
    else
        echo "❌ Testes falharam - enviando alerta"
        # Enviar notificação
    fi

    sleep 300  # 5 minutos
done
```

### Análise de Performance

```python
# analyze_performance.py
import json
from pathlib import Path

# Carregar último relatório JSON
reports_dir = Path("reports")
latest_report = max(reports_dir.glob("test_report_*.json"))

with open(latest_report) as f:
    data = json.load(f)

# Analisar tempos de resposta
for result in data["detailed_results"]:
    if result["response_time"] > 1.0:  # > 1 segundo
        print(f"⚠️ Endpoint lento: {result['endpoint']} ({result['response_time']:.3f}s)")
```

## 🤝 Contribuição

Para adicionar novos testes:

1. **Crie um novo tester** seguindo o padrão dos existentes
2. **Adicione configurações** em `test_config.py`
3. **Registre no runner** em `run_all_tests.py`
4. **Teste e documente** as mudanças

## 📞 Suporte

Para dúvidas ou problemas:

1. Consulte os logs em `reports/test_execution.log`
2. Execute com `--verbose` para mais detalhes
3. Verifique a configuração com `python test_config.py`
4. Consulte a documentação da API

---

**Desenvolvido para o Portal de Benefícios KNN** 🚀
