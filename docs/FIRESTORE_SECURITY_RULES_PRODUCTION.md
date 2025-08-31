# Regras de Segurança do Firestore - Banco de Produção (knn-benefits)

## Visão Geral

Este documento define as regras de segurança para o banco de dados Firestore de **produção** (`knn-benefits`). Estas regras são mais restritivas que as de desenvolvimento para garantir máxima segurança dos dados em produção.

## Configuração Atual

### Projeto Firebase
- **ID do Projeto**: `knn-benefits`
- **Ambiente**: Produção
- **Tenant ID**: `knn-benefits-tenant`

### Coleções Principais
- `students` - Dados dos alunos (74 registros)
- `employees` - Dados dos funcionários (12 registros)
- `partners` - Parceiros comerciais
- `promotions` - Promoções disponíveis
- `validation_codes` - Códigos de validação
- `redemptions` - Histórico de resgates

## Regras de Segurança para Produção

### 1. Regras Restritivas para Produção (RECOMENDADO)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Função auxiliar para verificar tenant válido
    function isValidTenant() {
      return resource.data.tenant_id == "knn-benefits-tenant";
    }

    // Função auxiliar para verificar se é admin
    function isAdmin() {
      return request.auth != null && 
             request.auth.token.role == "admin" &&
             request.auth.token.tenant_id == "knn-benefits-tenant";
    }

    // Função auxiliar para verificar se é o próprio usuário
    function isOwner(userId) {
      return request.auth != null && request.auth.uid == userId;
    }

    // Função para validar dados obrigatórios de estudantes
    function isValidStudentData() {
      return request.resource.data.keys().hasAll(['id', 'tenant_id', 'nome']) &&
             request.resource.data.tenant_id == "knn-benefits-tenant" &&
             request.resource.data.nome is string &&
             request.resource.data.nome.size() > 0;
    }

    // Função para validar dados obrigatórios de funcionários
    function isValidEmployeeData() {
      return request.resource.data.keys().hasAll(['id', 'tenant_id', 'nome', 'cargo']) &&
             request.resource.data.tenant_id == "knn-benefits-tenant" &&
             request.resource.data.nome is string &&
             request.resource.data.nome.size() > 0 &&
             request.resource.data.cargo is string &&
             request.resource.data.cargo.size() > 0;
    }

    // === COLEÇÃO STUDENTS ===
    match /students/{studentId} {
      // Leitura: próprio usuário ou admin
      allow read: if request.auth != null &&
                     (isOwner(studentId) || isAdmin()) &&
                     isValidTenant();

      // Criação: apenas admins com dados válidos
      allow create: if isAdmin() && isValidStudentData();

      // Atualização: próprio usuário (campos limitados) ou admin
      allow update: if request.auth != null &&
                       isValidTenant() &&
                       (isOwner(studentId) || isAdmin()) &&
                       isValidStudentData();

      // Exclusão: apenas admins
      allow delete: if isAdmin() && isValidTenant();
    }

    // === COLEÇÃO EMPLOYEES ===
    match /employees/{employeeId} {
      // Leitura: próprio usuário ou admin
      allow read: if request.auth != null &&
                     (isOwner(employeeId) || isAdmin()) &&
                     isValidTenant();

      // Criação: apenas admins com dados válidos
      allow create: if isAdmin() && isValidEmployeeData();

      // Atualização: próprio usuário (campos limitados) ou admin
      allow update: if request.auth != null &&
                       isValidTenant() &&
                       (isOwner(employeeId) || isAdmin()) &&
                       isValidEmployeeData();

      // Exclusão: apenas admins
      allow delete: if isAdmin() && isValidTenant();
    }

    // === COLEÇÃO PARTNERS ===
    match /partners/{partnerId} {
      // Leitura: usuários autenticados (para visualizar promoções)
      allow read: if request.auth != null;

      // Escrita: apenas administradores
      allow write: if isAdmin();
    }

    // === COLEÇÃO PROMOTIONS ===
    match /promotions/{promotionId} {
      // Leitura: usuários autenticados
      allow read: if request.auth != null;

      // Escrita: apenas administradores
      allow write: if isAdmin();
    }

    // === COLEÇÃO VALIDATION_CODES ===
    match /validation_codes/{codeId} {
      // Leitura: próprio usuário ou admin
      allow read: if request.auth != null &&
                     (isOwner(resource.data.student_id) ||
                      isOwner(resource.data.employee_id) ||
                      isAdmin());

      // Criação: usuários autenticados para si mesmos ou admins
      allow create: if request.auth != null &&
                       (request.resource.data.student_id == request.auth.uid ||
                        request.resource.data.employee_id == request.auth.uid ||
                        isAdmin()) &&
                       request.resource.data.tenant_id == "knn-benefits-tenant";

      // Atualização: apenas para marcar como usado
      allow update: if request.auth != null &&
                       (isOwner(resource.data.student_id) ||
                        isOwner(resource.data.employee_id) ||
                        isAdmin()) &&
                       // Só permite atualizar o campo 'used_at'
                       request.resource.data.diff(resource.data).affectedKeys().hasOnly(['used_at']);

      // Exclusão: apenas admins
      allow delete: if isAdmin();
    }

    // === COLEÇÃO REDEMPTIONS ===
    match /redemptions/{redemptionId} {
      // Leitura: próprio usuário ou admin
      allow read: if request.auth != null &&
                     (isOwner(resource.data.student_id) ||
                      isOwner(resource.data.employee_id) ||
                      isAdmin());

      // Criação: usuários autenticados para si mesmos
      allow create: if request.auth != null &&
                       (request.resource.data.student_id == request.auth.uid ||
                        request.resource.data.employee_id == request.auth.uid) &&
                       request.resource.data.tenant_id == "knn-benefits-tenant";

      // Atualização: apenas admins
      allow update: if isAdmin();

      // Exclusão: apenas admins
      allow delete: if isAdmin();
    }

    // Negar acesso a qualquer outra coleção
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

## Configurações de Autenticação

### Tokens Personalizados para Produção

Para produção, os tokens devem incluir informações específicas:

```python
# Token para administrador
custom_token = {
    "uid": "admin-user-id",
    "role": "admin",
    "tenant_id": "knn-benefits-tenant",
    "permissions": ["read_all", "write_all", "delete_all"]
}

# Token para aluno
custom_token = {
    "uid": "STD_XXXXXXXX",  # ID do estudante
    "role": "student",
    "tenant_id": "knn-benefits-tenant",
    "permissions": ["read_own", "update_own"]
}

# Token para funcionário
custom_token = {
    "uid": "EMP_XXXXXXXX",  # ID do funcionário
    "role": "employee",
    "tenant_id": "knn-benefits-tenant",
    "permissions": ["read_own", "update_own"]
}
```

## Validação dos Dados

### Campos Obrigatórios por Coleção

#### Students
- `id` (string) - ID único do estudante
- `tenant_id` (string) = "knn-benefits-tenant"
- `nome` (string) - Nome completo
- `created_at` (timestamp) - Data de criação
- `updated_at` (timestamp) - Data de atualização

#### Employees
- `id` (string) - ID único do funcionário
- `tenant_id` (string) = "knn-benefits-tenant"
- `nome` (string) - Nome completo
- `cargo` (string) - Cargo/função
- `active` (boolean) - Status ativo/inativo
- `created_at` (timestamp) - Data de criação
- `updated_at` (timestamp) - Data de atualização

### Regras de Validação Avançadas

```javascript
// Validação de email (se presente)
function isValidEmail(email) {
  return email.matches('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$');
}

// Validação de telefone brasileiro (se presente)
function isValidPhone(phone) {
  return phone.matches('^\\([0-9]{2}\\) [0-9]{4,5}-[0-9]{4}$');
}

// Validação de CPF hash
function isValidCPFHash(cpf_hash) {
  return cpf_hash is string && cpf_hash.size() == 64; // SHA-256
}
```

## Monitoramento e Auditoria

### Métricas Críticas para Produção
- **Operações negadas**: > 100/hora = Alerta
- **Uso de quota**: > 90% = Alerta crítico
- **Latência**: > 1000ms = Investigação
- **Tentativas de acesso não autorizado**: > 10/hora = Alerta de segurança

### Logs de Auditoria
```javascript
// Adicionar logs para operações sensíveis
allow delete: if isAdmin() && 
                 debug('AUDIT: Admin ' + request.auth.uid + ' deleting document ' + resource.id);
```

## Backup e Recuperação

### Configurações Recomendadas
- **Backup automático**: Diário às 02:00 UTC
- **Retenção**: 30 dias para backups diários, 12 meses para backups mensais
- **Teste de recuperação**: Mensal

### Comandos de Backup
```bash
# Exportar dados
gcloud firestore export gs://knn-benefits-backup/$(date +%Y-%m-%d) --project=knn-benefits

# Importar dados (em caso de recuperação)
gcloud firestore import gs://knn-benefits-backup/2025-01-28 --project=knn-benefits
```

## Índices Recomendados

### Índices Compostos Necessários
```javascript
// Para consultas por tenant_id + status
{
  "collectionGroup": "students",
  "queryScope": "COLLECTION",
  "fields": [
    {"fieldPath": "tenant_id", "order": "ASCENDING"},
    {"fieldPath": "active", "order": "ASCENDING"}
  ]
}

// Para consultas de promoções ativas
{
  "collectionGroup": "promotions",
  "queryScope": "COLLECTION",
  "fields": [
    {"fieldPath": "active", "order": "ASCENDING"},
    {"fieldPath": "valid_to", "order": "DESCENDING"}
  ]
}
```

## Implementação das Regras

### 1. Via Firebase CLI
```bash
# Fazer deploy das regras
firebase deploy --only firestore:rules --project=knn-benefits

# Testar regras antes do deploy
firebase firestore:rules:test --project=knn-benefits
```

### 2. Via Console Firebase
1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Selecione o projeto `knn-benefits`
3. Vá para "Firestore Database" > "Regras"
4. Cole as regras acima
5. Clique em "Publicar"

## Testes de Segurança

### Casos de Teste Obrigatórios

1. **Usuário não autenticado**
   - ❌ Deve ser negado acesso a todas as coleções

2. **Usuário autenticado sem role**
   - ❌ Deve ser negado acesso a dados sensíveis
   - ✅ Pode ler promoções públicas

3. **Administrador**
   - ✅ Deve ter acesso completo com tenant correto
   - ❌ Deve ser negado acesso com tenant incorreto

4. **Aluno**
   - ✅ Deve acessar apenas próprios dados
   - ❌ Deve ser negado acesso a dados de outros alunos
   - ✅ Pode ler parceiros e promoções

5. **Funcionário**
   - ✅ Deve acessar apenas próprios dados
   - ❌ Deve ser negado acesso a dados de outros funcionários
   - ✅ Pode ler parceiros e promoções

### Script de Teste Automatizado
```python
#!/usr/bin/env python3
# test_firestore_security.py

import firebase_admin
from firebase_admin import auth, firestore
import pytest

def test_unauthenticated_access():
    """Testa que usuários não autenticados são bloqueados"""
    # Implementar teste
    pass

def test_admin_access():
    """Testa que admins têm acesso completo"""
    # Implementar teste
    pass

def test_student_isolation():
    """Testa que alunos só acessam próprios dados"""
    # Implementar teste
    pass
```

## Checklist de Implementação

### Pré-Deploy
- [ ] Revisar todas as regras de segurança
- [ ] Testar regras em ambiente de staging
- [ ] Validar tokens de autenticação
- [ ] Configurar índices necessários
- [ ] Testar performance das consultas

### Deploy
- [ ] Fazer backup dos dados atuais
- [ ] Implementar regras em horário de baixo tráfego
- [ ] Monitorar logs por 24h após deploy
- [ ] Validar funcionamento de todas as operações

### Pós-Deploy
- [ ] Configurar alertas de monitoramento
- [ ] Documentar mudanças implementadas
- [ ] Treinar equipe sobre novas regras
- [ ] Agendar revisão de segurança mensal

## Contatos e Suporte

- **Console Firebase**: https://console.firebase.google.com/project/knn-benefits
- **Documentação**: https://firebase.google.com/docs/firestore/security/rules-structure
- **Monitoramento**: Google Cloud Console > Firestore

---

**Data de Criação**: 28 de Janeiro de 2025
**Última Atualização**: 28 de Janeiro de 2025
**Versão**: 1.0
**Ambiente**: Produção (knn-benefits)
**Status**: Pronto para implementação