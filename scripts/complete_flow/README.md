# Fluxo Completo de Autenticação e Acesso aos Benefícios

Este documento descreve a solução completa implementada para resolver os problemas de autenticação e acesso aos benefícios no sistema KNN Portal Journey Club Backend.

## Problemas Identificados e Soluções

### 1. ImportError do Rate Limiter

**Problema**: `ImportError` ao tentar importar `RateLimitMiddleware` de `src.utils.rate_limit`
**Solução**: Corrigido em `src/main.py` alterando a importação para `limiter` e configurando diretamente no app FastAPI

### 2. Configuração JWT_SECRET_KEY

**Problema**: Verificação se a chave secreta JWT estava configurada corretamente
**Solução**: Confirmado que a variável de ambiente estava definida corretamente

### 3. Problema de Fuso Horário JWT

**Problema**: Erro "The token is not yet valid (iat)" devido a diferença de horário
**Solução**: Modificado `generate_token.py` para usar `datetime.now(timezone.utc)` nos campos `iat` e `exp`

### 4. Erro 404 'PARTNER_NOT_FOUND'

**Problema**: Parceiro não encontrado mesmo existindo no Firestore
**Solução**: Identificado problema de incompatibilidade de `tenant_id`

### 5. Incompatibilidade de tenant_id

**Problema**: JWT usava tenant 'knn' enquanto benefícios usavam 'knn-dev-tenant'
**Soluções**:

- Alterado token JWT para usar tenant 'knn-dev-tenant'
- Corrigido documento Firestore para ter `tenant_id` no nível raiz

## Scripts Criados

### 1. `generate_token.py`

Gera tokens JWT válidos com:

- Fuso horário UTC correto
- Tenant 'knn-dev-tenant'
- Expiração de 24 horas

### 2. `test_direct_endpoint.py`

Testa o endpoint `/v1/admin/benefits/{partner_id}/{benefit_id}` com:

- Carregamento automático do token
- Logs detalhados da requisição
- Exibição completa da resposta

### 3. `check_tenant.py`

Verifica o `tenant_id` configurado nos documentos do Firestore

### 4. `fix_document_tenant.py`

Corrige o `tenant_id` do documento no Firestore, adicionando:

- `tenant_id` no nível raiz do documento
- `system.tenant_id` para compatibilidade

### 5. `debug_firestore_structure.py`

Analisa a estrutura dos documentos no Firestore para debugging

## Fluxo de Autenticação Final

1. **Geração do Token**: Script gera JWT com tenant correto e fuso horário UTC
2. **Validação**: Sistema valida token JWT local como fallback do Firebase
3. **Autorização**: Verifica se `tenant_id` do usuário corresponde ao do documento
4. **Acesso**: Retorna dados do benefício se autorizado

## Resultado Final

✅ **Endpoint funcionando**: `/v1/admin/benefits/PTN_T4L5678_TEC/BNF_FD7025_DC`
✅ **Autenticação**: JWT local validado com sucesso
✅ **Autorização**: tenant_id compatível entre token e documento
✅ **Dados**: Benefício retornado com estrutura completa

## Exemplo de Resposta Bem-sucedida

```json
{
  "data": {
    "title": "Benefício de Teste Admin",
    "description": "Descrição do benefício de teste criado pelo admin",
    "benefit_id": "BNF_FD7025_DC",
    "partner_id": "PTN_T4L5678_TEC",
    "system": {
      "tenant_id": "knn-dev-tenant",
      "status": "active",
      "type": "percentage",
      "category": "desconto"
    },
    "configuration": {
      "value": 15,
      "value_type": "percentage",
      "calculation_method": "final_amount"
    },
    "dates": {
      "created_at": "2025-09-29T21:15:56.966802+00:00",
      "updated_at": "2025-09-29T21:15:56.966802+00:00",
      "valid_from": "2025-01-01T00:00:00Z",
      "valid_until": null
    }
  }
}
```

## Comandos para Teste

```bash
# 1. Gerar token
python scripts/complete_flow/generate_token.py

# 2. Testar endpoint
python scripts/complete_flow/test_direct_endpoint.py

# 3. Verificar tenant (se necessário)
python scripts/complete_flow/check_tenant.py

# 4. Corrigir tenant do documento (se necessário)
python scripts/complete_flow/fix_document_tenant.py
```

## Configurações Importantes

- **Tenant**: 'knn-dev-tenant' (deve ser consistente entre JWT e Firestore)
- **JWT Secret**: Configurado via variável de ambiente `JWT_SECRET_KEY`
- **Fuso Horário**: UTC para evitar problemas de validação temporal
- **Firestore**: Documento deve ter `tenant_id` no nível raiz e em `system.tenant_id`
