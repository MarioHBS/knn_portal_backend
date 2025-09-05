# Regras de Segurança do Firestore - Banco de Teste (Default)

## Visão Geral

Este documento define as regras de segurança recomendadas para o banco de dados Firestore de **teste** (`knn-portal-dev`). Estas regras são mais permissivas que as de produção para facilitar o desenvolvimento e testes, mas ainda mantêm controles básicos de segurança.

## Configuração Atual

### Projeto Firebase
- **ID do Projeto**: `knn-portal-dev`
- **Ambiente**: Desenvolvimento/Teste
- **Tenant ID**: `knn-dev-tenant`

### Coleções Principais
- `tenants` - Metadados das escolas/unidades
- `metadata` - Metadados das coleções
- `students` - Dados dos alunos (74 registros)
- `employees` - Dados dos funcionários (12 registros)
- `partners` - Parceiros comerciais
- `promotions` - Promoções disponíveis
- `validation_codes` - Códigos de validação
- `redemptions` - Histórico de resgates

## Regras de Segurança Recomendadas

### 1. Regras Básicas para Desenvolvimento

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Regra geral para desenvolvimento - mais permissiva
    match /{document=**} {
      // Permite leitura e escrita para usuários autenticados
      allow read, write: if request.auth != null;
    }

    // Regras específicas por coleção
    match /students/{studentId} {
      // Permite operações para usuários autenticados
      allow read, write: if request.auth != null
        && resource.data.tenant_id == "knn-dev-tenant";

      // Permite criação de novos documentos
      allow create: if request.auth != null
        && request.resource.data.tenant_id == "knn-dev-tenant";
    }

    match /employees/{employeeId} {
      // Permite operações para usuários autenticados
      allow read, write: if request.auth != null
        && resource.data.tenant_id == "knn-dev-tenant";

      // Permite criação de novos documentos
      allow create: if request.auth != null
        && request.resource.data.tenant_id == "knn-dev-tenant";
    }

    match /partners/{partnerId} {
      // Permite leitura para todos os usuários autenticados
      allow read: if request.auth != null;

      // Permite escrita apenas para administradores
      allow write: if request.auth != null
        && request.auth.token.role == "admin";
    }

    match /promotions/{promotionId} {
      // Permite leitura para todos os usuários autenticados
      allow read: if request.auth != null;

      // Permite escrita apenas para administradores
      allow write: if request.auth != null
        && request.auth.token.role == "admin";
    }

    match /validation_codes/{codeId} {
      // Permite operações apenas para o próprio usuário
      allow read, write: if request.auth != null
        && (resource.data.student_id == request.auth.uid
            || resource.data.employee_id == request.auth.uid);
    }

    match /redemptions/{redemptionId} {
      // Permite leitura para o próprio usuário
      allow read: if request.auth != null;

      // Permite criação de novos resgates
      allow create: if request.auth != null;
    }
  }
}
```

### 2. Regras Alternativas - Mais Restritivas

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Função auxiliar para verificar tenant
    function isValidTenant() {
      return resource.data.tenant_id == "knn-dev-tenant";
    }

    // Função auxiliar para verificar se é admin
    function isAdmin() {
      return request.auth != null && request.auth.token.role == "admin";
    }

    // Função auxiliar para verificar se é o próprio usuário
    function isOwner(userId) {
      return request.auth != null && request.auth.uid == userId;
    }

    match /students/{studentId} {
      allow read: if request.auth != null && isValidTenant();
      allow write: if isAdmin() && isValidTenant();
      allow create: if isAdmin() && request.resource.data.tenant_id == "knn-dev-tenant";
    }

    match /employees/{employeeId} {
      allow read: if request.auth != null && isValidTenant();
      allow write: if isAdmin() && isValidTenant();
      allow create: if isAdmin() && request.resource.data.tenant_id == "knn-dev-tenant";
    }

    match /partners/{partnerId} {
      allow read: if request.auth != null;
      allow write: if isAdmin();
    }

    match /promotions/{promotionId} {
      allow read: if request.auth != null;
      allow write: if isAdmin();
    }

    match /validation_codes/{codeId} {
      allow read, write: if request.auth != null &&
        (isOwner(resource.data.student_id) || isAdmin());
    }

    match /redemptions/{redemptionId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update, delete: if isAdmin();
    }
  }
}
```

### 3. Regras Ultra-Permissivas (Apenas para Testes Iniciais)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // ⚠️ ATENÇÃO: Usar apenas para testes iniciais
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

## Configurações de Autenticação

### Tokens Personalizados para Teste

Para testar as regras com diferentes perfis, configure tokens personalizados:

```python
# Exemplo de token para administrador
custom_token = {
    "uid": "admin-user-id",
    "role": "admin",
    "tenant_id": "knn-dev-tenant"
}

# Exemplo de token para aluno
custom_token = {
    "uid": "STD_A3C1M7L7_S4",
    "role": "student",
    "tenant_id": "knn-dev-tenant"
}

# Exemplo de token para funcionário
custom_token = {
    "uid": "EMP_A0A0O007_AP",
    "role": "employee",
    "tenant_id": "knn-dev-tenant"
}
```

## Validação dos Dados

### Campos Obrigatórios por Coleção

#### Students
- `id` (string)
- `tenant_id` (string) = "knn-dev-tenant"
- `nome` (string)
- `livro` (string)
- `ocupacao` (string)
- `created_at` (timestamp)
- `updated_at` (timestamp)

#### Employees
- `id` (string)
- `tenant_id` (string) = "knn-dev-tenant"
- `nome` (string)
- `cargo` (string)
- `active` (boolean)
- `created_at` (timestamp)
- `updated_at` (timestamp)

### Regras de Validação de Dados

```javascript
// Exemplo de validação para estudantes
match /students/{studentId} {
  allow create, update: if request.auth != null &&
    request.resource.data.keys().hasAll(['id', 'tenant_id', 'nome', 'livro']) &&
    request.resource.data.tenant_id == "knn-dev-tenant" &&
    request.resource.data.nome is string &&
    request.resource.data.nome.size() > 0;
}
```

## Monitoramento e Logs

### Métricas Importantes
- Número de operações de leitura/escrita por coleção
- Tentativas de acesso negadas
- Uso de quota do Firestore
- Latência das consultas

### Alertas Recomendados
- Mais de 1000 operações negadas por hora
- Uso de quota acima de 80%
- Latência média acima de 500ms

## Testes das Regras

### Comandos para Testar

```bash
# Instalar o emulador do Firebase
npm install -g firebase-tools

# Inicializar o projeto
firebase init firestore

# Executar o emulador
firebase emulators:start --only firestore

# Testar regras específicas
firebase firestore:rules:test --project=knn-portal-dev
```

### Casos de Teste

1. **Usuário não autenticado**
   - Deve ser negado acesso a todas as coleções

2. **Usuário autenticado sem role**
   - Deve ter acesso de leitura às coleções públicas
   - Deve ser negado acesso de escrita

3. **Administrador**
   - Deve ter acesso completo a todas as coleções

4. **Aluno**
   - Deve ter acesso aos próprios dados
   - Deve ter acesso de leitura a parceiros e promoções

5. **Funcionário**
   - Deve ter acesso aos próprios dados
   - Deve ter acesso de leitura a parceiros e promoções

## Migração para Produção

### Diferenças Principais
- Regras mais restritivas
- Validação de dados mais rigorosa
- Logs de auditoria obrigatórios
- Backup automático configurado
- Monitoramento 24/7

### Checklist de Migração
- [ ] Testar todas as regras no ambiente de teste
- [ ] Validar performance das consultas
- [ ] Configurar índices necessários
- [ ] Implementar logs de auditoria
- [ ] Configurar alertas de segurança
- [ ] Documentar todas as mudanças

## Próximos Passos

1. **Implementar regras básicas** (Opção 1 recomendada)
2. **Configurar autenticação de teste**
3. **Testar operações CRUD via API**
4. **Monitorar performance e segurança**
5. **Ajustar regras conforme necessário**
6. **Preparar migração para produção**

## Contatos e Suporte

- **Documentação Firebase**: https://firebase.google.com/docs/firestore/security/rules-structure
- **Console Firebase**: https://console.firebase.google.com/project/knn-portal-dev
- **Emulador Local**: http://localhost:4000/firestore

---

**Data de Criação**: 28 de Agosto de 2025
**Última Atualização**: 28 de Agosto de 2025
**Versão**: 1.0
**Ambiente**: Desenvolvimento/Teste
