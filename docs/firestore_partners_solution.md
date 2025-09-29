# Solução: Endpoint /admin/partners retornando 0 parceiros

## Problema Identificado

O endpoint `/admin/partners` estava retornando 0 parceiros mesmo com dados corretos no Firestore devido à **falta de um índice composto** necessário para a consulta com filtros e ordenação.

## Análise Realizada

### 1. Verificação dos Dados
- ✅ 11 parceiros existem no Firestore
- ✅ Todos têm `tenant_id = "knn-dev-tenant"`
- ✅ Todos têm `active = True` (corrigido de `None`)

### 2. Teste das Consultas
- ✅ Consulta simples: `tenant_id == "knn-dev-tenant"` → 11 resultados
- ✅ Consulta com filtro: `tenant_id == "knn-dev-tenant" AND active == True` → 11 resultados
- ❌ Consulta com ordenação: `tenant_id == "knn-dev-tenant" AND active == True ORDER BY trade_name` → **Erro: índice necessário**

### 3. Causa Raiz
O `PartnersService.list_partners_common()` usa ordenação por `trade_name` quando `enable_ordering=True`, mas o Firestore requer um **índice composto** para consultas que combinam:
- Filtros em múltiplos campos (`tenant_id`, `active`)
- Ordenação (`trade_name`)

## Solução Implementada

### 1. Correção dos Dados
Executado script para corrigir o campo `active` dos parceiros:
```python
# Antes: active = None
# Depois: active = True
```

### 2. Criação do Índice Composto
**Índice necessário no Firestore:**
- Collection: `partners`
- Fields:
  - `tenant_id` (Ascending)
  - `active` (Ascending)
  - `trade_name` (Ascending)

**Link direto para criar o índice:**
```
https://console.firebase.google.com/v1/r/project/knn-benefits/firestore/indexes?create_composite=Ck1wcm9qZWN0cy9rbm4tYmVuZWZpdHMvZGF0YWJhc2VzLyhkZWZhdWx0KS9jb2xsZWN0aW9uR3JvdXBzL3BhcnRuZXJzL2luZGV4ZXMvXxABGgoKBmFjdGl2ZRABGg0KCXRlbmFudF9pZBABGg4KCnRyYWRlX25hbWUQARoMCghfX25hbWVfXxAB
```

### 3. Alternativas para Criar o Índice

#### Opção 1: Console do Firebase
1. Acessar [Firebase Console](https://console.firebase.google.com)
2. Ir para Firestore Database > Indexes
3. Criar índice composto com os campos:
   - `tenant_id` (Ascending)
   - `active` (Ascending)
   - `trade_name` (Ascending)

#### Opção 2: Firebase CLI
```bash
firebase firestore:indexes
```

## Arquivos Criados

### Scripts de Diagnóstico
- `scripts/temp/check_partners_firestore.py` - Verificação inicial dos dados
- `scripts/temp/fix_partners_active_field.py` - Correção do campo `active`
- `scripts/temp/check_partners_tenant_field.py` - Verificação do campo `tenant_id`
- `scripts/temp/debug_firestore_simple.py` - Debug das consultas
- `scripts/temp/create_firestore_index.py` - Informações sobre o índice

### Testes
- `scripts/temp/test_admin_simple_new.py` - Teste do endpoint após correções

## Fluxo da Consulta

```python
# PartnersService.list_partners_common()
filters = [("active", "==", True)]
order_by = [("trade_name", "ASCENDING")] if enable_ordering else None

# FirestoreClient.query_documents()
# 1. Aplica filtro obrigatório: tenant_id == current_user.tenant
# 2. Aplica filtros adicionais: active == True
# 3. Aplica ordenação: ORDER BY trade_name
# ❌ FALHA: Requer índice composto
```

## Status da Solução

- ✅ **Dados corrigidos**: Campo `active` definido como `True`
- ⏳ **Índice pendente**: Aguardando criação do índice composto no Console do Firebase
- 🧪 **Teste**: Endpoint funcionará após criação do índice

## Próximos Passos

1. **Criar o índice composto** usando o link fornecido ou Console do Firebase
2. **Aguardar a criação** (pode levar alguns minutos)
3. **Testar o endpoint** `/admin/partners` novamente
4. **Verificar** se retorna os 11 parceiros esperados

## Lições Aprendidas

1. **Firestore requer índices compostos** para consultas complexas
2. **Sempre verificar dados** antes de assumir problemas de código
3. **Debugar consultas** diretamente no Firestore para isolar problemas
4. **Documentar índices necessários** para facilitar deploy em outros ambientes