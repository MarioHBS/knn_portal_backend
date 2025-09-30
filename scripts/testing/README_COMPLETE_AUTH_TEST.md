# Script de Teste Completo de Autenticação - Portal KNN

Este documento descreve o uso do script `complete_auth_flow_test.py`, que simula o processo completo de autenticação do Portal KNN, incluindo autenticação Firebase, obtenção de tokens JWT e testes de endpoints autenticados.

## 📋 Visão Geral

O script executa o seguinte fluxo de autenticação:

1. **Autenticação Firebase**: Usa a REST API do Firebase para autenticar com email/senha
2. **Captura do Firebase Token**: Obtém o token de identificação do Firebase
3. **Login no Backend**: Chama `/users/login` para trocar o Firebase token por JWT
4. **Testes de Endpoints**: Usa o JWT para testar endpoints autenticados

## 🚀 Configuração Inicial

### Pré-requisitos

1. **Ambiente Virtual Ativo**:

   ```bash
   .venv\Scripts\activate
   ```

2. **Firebase API Key Configurada**:

   ```bash
   set FIREBASE_API_KEY=sua_api_key_aqui
   ```

   Ou adicione ao arquivo `.env`:

   ```env
   FIREBASE_API_KEY=sua_api_key_aqui
   ```

3. **Backend Rodando**:

   ```bash
   python scripts/run_server.py
   ```

### Script de Configuração Automática

Execute o script de configuração para verificar e configurar o ambiente:

```bash
python scripts/testing/setup_auth_test_env.py
```

## 👥 Usuários de Teste Pré-definidos

O script inclui os seguintes usuários de teste:

| Usuário | Email | Senha | Role | Descrição |
|---------|-------|-------|------|-----------|
| `parceiro_teste` | parceiro.teste@journeyclub.com.br | Tp654321 | partner | Usuário parceiro (padrão) |
| `admin_teste` | admin.teste@journeyclub.com.br | Admin123 | admin | Usuário administrador |
| `estudante_teste` | estudante.teste@journeyclub.com.br | Tp654321 | student | Usuário estudante |
| `funcionario_teste` | funcionario.teste@journeyclub.com.br | Tp54321 | employee | Usuário funcionário |

## 🎯 Modos de Execução

### Modo Interativo (Padrão)

Executa o script e permite selecionar o usuário:

```bash
python scripts/testing/complete_auth_flow_test.py
```

O script exibirá um menu para seleção do usuário:

```text
SELEÇÃO DE USUÁRIO PARA TESTE
==================================================

Usuários disponíveis para teste:
--------------------------------------------------
1. Usuário parceiro para testes
   Email: parceiro.teste@journeyclub.com.br
   Role: partner

2. Usuário administrador para testes
   Email: admin.teste@journeyclub.com.br
   Role: admin

...

Selecione um usuário (1-4) ou 'q' para sair:
```

### Modo Automático

Executa automaticamente com o usuário padrão (parceiro_teste):

```bash
python scripts/testing/complete_auth_flow_test.py --auto
```

### Teste Rápido

Use o script de teste rápido gerado automaticamente:

```bash
python scripts/testing/quick_auth_test.py
```

## 📊 Fluxo de Teste Detalhado

### Etapa 1: Validação do Ambiente

- ✅ Verifica se `FIREBASE_API_KEY` está configurada
- ✅ Testa conectividade com o backend (`/health`)

### Etapa 2: Autenticação Firebase

- 🔐 Envia credenciais para `https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword`
- 🎫 Obtém o Firebase ID Token
- ⏱️ Timeout de 30 segundos

### Etapa 3: Login no Backend

- 📤 Envia Firebase token para `/v1/users/login`
- 🎫 Obtém JWT token do backend
- 👤 Captura informações do usuário

### Etapa 4: Testes de Endpoints Autenticados

- 🔍 Testa endpoints básicos: `/users/me`, `/health`
- 🎯 Testa endpoints específicos por role:
  - **Student**: `/students/profile`, `/students/benefits`
  - **Partner**: `/partners/profile`, `/partners/benefits`
  - **Admin**: `/admin/users`, `/admin/stats`
  - **Employee**: `/employees/profile`

## 📈 Relatórios e Logs

### Saída no Console

O script fornece logs detalhados em tempo real:

```
[14:30:15] ℹ️ Iniciando autenticação Firebase para: parceiro.teste@journeyclub.com.br
[14:30:16] ✅ Autenticação Firebase bem-sucedida
[14:30:16] ℹ️ Token Firebase obtido: eyJhbGciOiJSUzI1NiIs...
[14:30:16] ℹ️ Iniciando login no backend
[14:30:17] ✅ Login no backend bem-sucedido
[14:30:17] ℹ️ JWT Token obtido: eyJhbGciOiJIUzI1NiIs...
```

### Relatório JSON

Cada execução gera um relatório detalhado em JSON:

```
scripts/testing/auth_test_report_20250106_143020.json
```

Estrutura do relatório:

```json
{
  "timestamp": "20250106_143020",
  "summary": {
    "total_tests": 1,
    "successful_tests": 1,
    "failed_tests": 0,
    "success_rate": 100.0
  },
  "results": [
    {
      "user": "parceiro_teste",
      "email": "parceiro.teste@journeyclub.com.br",
      "role": "partner",
      "success": true,
      "steps": [
        {"step": "validate_environment", "success": true},
        {"step": "firebase_auth", "success": true},
        {"step": "backend_login", "success": true}
      ],
      "tokens": {
        "firebase_token": "eyJhbGciOiJSUzI1NiIs...",
        "jwt_token": "eyJhbGciOiJIUzI1NiIs..."
      },
      "user_info": {
        "email": "parceiro.teste@journeyclub.com.br",
        "role": "partner"
      },
      "endpoints_tested": [
        {"endpoint": "/users/me", "success": true, "data_received": true},
        {"endpoint": "/health", "success": true, "data_received": true}
      ]
    }
  ]
}
```

## 🔧 Configurações Avançadas

### Variáveis de Ambiente

```env
# Obrigatória
FIREBASE_API_KEY=sua_api_key_do_firebase

# Opcionais
BACKEND_BASE_URL=http://localhost:8080/v1  # URL do backend
FIREBASE_PROJECT_ID=knn-benefits           # ID do projeto Firebase
```

### Personalização de Usuários

Para adicionar novos usuários de teste, edite o dicionário `TEST_USERS` no script:

```python
TEST_USERS = {
    "novo_usuario": {
        "email": "novo@exemplo.com",
        "password": "senha123",
        "role": "student",
        "description": "Novo usuário de teste"
    }
}
```

### Timeout e Retry

O script usa configurações robustas de rede:

```python
# Retry automático para falhas de rede
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)

# Timeout de 30 segundos para requisições
timeout=30
```

## 🐛 Solução de Problemas

### Erro: "FIREBASE_API_KEY não encontrada"

**Solução**:
1. Configure a variável de ambiente:
   ```bash
   set FIREBASE_API_KEY=sua_api_key
   ```
2. Ou adicione ao arquivo `.env`
3. Execute o script de configuração: `python scripts/testing/setup_auth_test_env.py`

### Erro: "Backend não está acessível"

**Solução**:
1. Verifique se o backend está rodando:
   ```bash
   python scripts/run_server.py
   ```
2. Teste manualmente: `curl http://localhost:8080/v1/health`

### Erro: "Credenciais inválidas"

**Possíveis causas**:
- Usuário não existe no Firebase
- Senha incorreta
- Projeto Firebase incorreto
- API Key inválida

**Solução**:
1. Verifique as credenciais no Firebase Console
2. Confirme o projeto Firebase (`knn-benefits`)
3. Teste com outro usuário

### Erro: "Token Firebase inválido"

**Possíveis causas**:
- Token expirado
- Configuração incorreta do backend
- Problemas de sincronização de horário

**Solução**:
1. Execute o teste novamente (tokens são renovados automaticamente)
2. Verifique a configuração do Firebase no backend

## 📚 Arquivos Relacionados

- `complete_auth_flow_test.py` - Script principal de teste
- `setup_auth_test_env.py` - Script de configuração do ambiente
- `quick_auth_test.py` - Script de teste rápido (gerado automaticamente)
- `test_firebase_login.py` - Teste específico do Firebase
- `test_config.py` - Configurações de teste

## 🔄 Integração com CI/CD

Para usar em pipelines automatizados:

```yaml
# GitHub Actions exemplo
- name: Teste de Autenticação
  run: |
    python scripts/testing/complete_auth_flow_test.py --auto
  env:
    FIREBASE_API_KEY: ${{ secrets.FIREBASE_API_KEY }}
```

## 📞 Suporte

Para problemas ou dúvidas:

1. Verifique os logs detalhados no console
2. Consulte o relatório JSON gerado
3. Execute o script de configuração para diagnóstico
4. Verifique a documentação do Firebase Auth

## 🎯 Próximos Passos

Após um teste bem-sucedido, você pode:

1. **Integrar com Frontend**: Use os tokens obtidos para testar a integração
2. **Testes Automatizados**: Incorpore o script em sua suíte de testes
3. **Monitoramento**: Use os relatórios para monitorar a saúde da autenticação
4. **Desenvolvimento**: Use os tokens para desenvolvimento local

---

**Versão**: 1.0
**Data**: 2025-01-06
**Autor**: Sistema de Testes KNN
