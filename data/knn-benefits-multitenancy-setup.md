
# KNN Benefits — Guia de Configuração (Multi-tenant com JWT + Firestore "flat")

> **Arquitetura atual**
>
> - **Coleções globais** por domínio de dados (ex.: `students`, `employees`, `partners`, `benefits`, `redemptions`), **cada documento com `tenant_id`**.
> - **Autenticação** com **JWT + JWKS + Firebase Admin SDK**: implementação atual mantida até expansão do projeto.
> - **Papéis (roles)**: `admin` (Administrador), `student` (Aluno), `employee` (Funcionário), `partner` (Parceiro).
> - **Benefícios**: criados por Parceiros, com *público-alvo* (`audience`) distinto para **Alunos** e **Funcionários**.
> - **Identity Platform**: planejado para implementação futura após expansão para 5+ escolas.

---

## 0) Pré-requisitos e visão geral

- **Front-end**: React + Vite + TypeScript (Firebase Web v9).
- **Back-end**: FastAPI (Python) em Cloud Run.
- **Banco**: Firestore (produção), com **`tenant_id`** em todos os documentos.
- **Replica/BI** (opcional): exportação diária para PostgreSQL (BigQuery/Cloud SQL) mantendo `tenant_id`.
- **Segredos**: Service Account (Admin SDK) via Secret Manager montado no contêiner.
- **Domínios**: `journeyclub.com.br` com subdomínios (ex.: `saoluis.journeyclub.com.br`) ou caminhos (`/t/{tenantId}`) para identificar o *tenant*.

---

## 1) Autenticação Atual (JWT + Firebase Admin SDK)

### 1.1 Implementação Atual

1. **JWT + JWKS**: Autenticação baseada em tokens JWT com validação via JWKS.
2. **Firebase Admin SDK**: Gerenciamento de usuários e validação de tokens.
3. **Tenant ID**: Identificação do tenant via `tenant_id` nos custom claims do token.

### 1.2 Identity Platform (Implementação Futura)

> **Nota**: Identity Platform será implementado apenas após expansão para 5+ escolas.

1. Ativar **Identity Platform** no Google Cloud Console.
2. Criar um *tenant* por escola (ex.: `knn_ma_sjr_cohatrac`, `knn_imperatriz`).
3. Em cada *tenant*, habilitar os provedores de login (e-mail/senha; Google, etc.).
4. Ajuste as **templates de e-mail** por *tenant* (opcional, branding por escola).

### 1.3 Como o front-end escolhe o tenant (Implementação Futura)

> **Nota**: Esta seção se aplica à futura implementação com Identity Platform.

- Detecte a escola pelo **subdomínio** ou pela **rota** (`/t/{tenant}`).
- Antes de qualquer ação de login, **defina `auth.tenantId`** no SDK web.
- **Importante:** `auth.tenantId` **não persiste** após reload; reatribua no *bootstrap* da aplicação.

```ts
// src/auth/tenant.ts (implementação futura)
import { getAuth } from "firebase/auth";

export function setTenantForAuth(tenantId: string | null) {
  const auth = getAuth();
  auth.tenantId = tenantId; // null para superadmin/console global
}
```

### 1.4 Papéis e *custom claims*

- Na implementação atual (JWT), use **custom claims** no ID token (ex.: `roles`, `partner_ids`, `tenant_id`).
- Na futura implementação com Identity Platform, os custom claims continuam funcionando.
- Ex.: `roles: ["admin"]`, `["partner"]`, `["student"]`, `["employee"]`.
- `partner_ids` restringe quais benefícios/resgates um parceiro pode alterar/ver.

### 1.5 Gerenciamento de Senhas Temporárias

> **Nova funcionalidade**: Sistema de senhas temporárias seguras para cadastro inicial de alunos e funcionários.

#### 1.5.1 Política de Senhas Temporárias

**Características das senhas temporárias:**

- **Complexidade**: Com 8 caracteres com letras maiúsculas, minúsculas e números, sem símbolos na temporária
- **Expiração**: 48 horas após geração
- **Uso único**: Senha deve ser alterada no primeiro acesso
- **Geração**: Apenas pelo Administrador via endpoint seguro
- **Armazenamento**: **NÃO armazenadas diretamente no sistema**. O Firebase Admin SDK cria automaticamente o usuário no serviço de autenticação, garantindo a segurança das credenciais

#### 1.5.2 Fluxo de Cadastro Inicial

**Processo para novos usuários:**

1. **Administrador** acessa endpoint `/admin/users/create-with-temp-password`
2. Sistema gera senha temporária segura automaticamente
3. **Firebase Admin SDK** cria usuário no Firebase Authentication com a senha temporária
4. Usuário recebe credenciais via email/SMS seguro
5. No primeiro login, sistema força redefinição de senha
6. Senha temporária é invalidada após uso ou expiração

#### 1.5.3 Modelo de Dados para Senhas Temporárias

**Campos adicionais nos documentos de usuários:**

```json
{
  "tenant_id": "knn_ma_sjr_cohatrac",
  "uid": "auth_uid_usuario",
  "name": "Nome do Usuário",
  "email": "usuario@exemplo.com",
  "temp_password": {
    "hash": "$2b$12$...",           // Hash da senha temporária
    "salt": "random_salt_value",    // Salt único
    "expires_at": 1722643200000,    // Timestamp de expiração
    "used": false,                  // Flag de uso
    "created_by": "admin_uid",      // Quem criou
    "created_at": 1722556800000     // Quando foi criada
  },
  "password_reset_required": true,  // Força reset no login
  "status": "pending_activation",   // Status específico
  "created_at": 1722556800000,
  "updated_at": 1722556800000
}
```

#### 1.5.4 Endpoints para Gerenciamento

**Novos endpoints administrativos:**

- `POST /admin/users/create-student-temp` - Criar aluno com senha temporária
- `POST /admin/users/create-employee-temp` - Criar funcionário com senha temporária
- `POST /admin/users/{id}/reset-temp-password` - Gerar nova senha temporária
- `GET /admin/users/pending-activation` - Listar usuários pendentes
- `POST /auth/activate-account` - Ativar conta com senha temporária

#### 1.5.5 Segurança e Auditoria

**Medidas de segurança implementadas:**

- **Rate limiting**: Máximo 10 criações de usuários por hora por administrador
- **Logs de auditoria**: Registro completo de criação, uso e expiração
- **Notificação segura**: Envio de credenciais via canais criptografados
- **Validação de força**: Verificação automática da complexidade da senha
- **Cleanup automático**: Remoção de senhas expiradas após 7 dias

**Exemplo de log de auditoria:**

```json
{
  "timestamp": "2024-08-01T10:30:00Z",
  "tenant_id": "knn_ma_sjr_cohatrac",
  "action": "temp_password_created",
  "admin_uid": "admin123",
  "target_user_uid": "user456",
  "expires_at": "2024-08-02T10:30:00Z",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

---

## 2) Modelo de dados (coleções globais + `tenant_id`)

> **Regra de ouro:** **todo documento tem** `tenant_id: string`.
> Timestamps em millis (`created_at`, `updated_at`) e índices contemplando `tenant_id`.

### 2.1 Coleções principais

#### `students` (Alunos)

```json
{
  "tenant_id": "knn_ma_sjr_cohatrac",
  "uid": "auth_uid_aluno",
  "name": "Maria Silva",
  "email": "maria@exemplo.com",
  "status": "active",             // active | blocked | deleted
  "favorites": ["benefitIdA", "benefitIdB"],
  "created_at": 1719868800000,
  "updated_at": 1719868800000
}
```

#### `employees` (Funcionários)

```json
{
  "tenant_id": "knn_ma_sjr_cohatrac",
  "uid": "auth_uid_func",
  "name": "João Souza",
  "email": "joao@empresa.com",
  "status": "active",
  "created_at": 1719868800000,
  "updated_at": 1719868800000
}
```

#### `partners` (Parceiros)

```json
{
  "tenant_id": "knn_ma_sjr_cohatrac",
  "name": "Livraria Folha & Letra",
  "owner_uid": "auth_uid_parceiro",        // quem gerencia no balcão
  "cnpj": "00.000.000/0001-00",
  "contact": { "email": "contato@livraria.com", "phone": "+55..." },
  "address": "Rua X, 123, Centro",
  "status": "active",
  "created_at": 1719868800000,
  "updated_at": 1719868800000
}
```

#### `benefits` (Benefícios/Promoções)

```json
{
  "tenant_id": "knn_ma_sjr_cohatrac",
  "partner_id": "partnerDocId",
  "title": "Leve 2, pague 1",
  "description": "Válido em livros de até R$ 80",
  "audience": ["student", "employee"],  // escopo de público
  "validation": {
    "mode": "code|id",                  // código único ou validação por ID
    "per_user_limit": 2,               // Limite por usuário (-1 = ilimitado)
    "global_limit": 1000,              // Limite global (-1 = ilimitado)
    "valid_from": 1722470400000,
    "valid_to": 1730246400000
  },
  "status": "active",
  "created_at": 1719868800000,
  "updated_at": 1719868800000
}
```

**Nota sobre Limites:**

- Para indicar **limites ilimitados**, use o valor `-1` nos campos `per_user_limit` e `global_limit`
- Exemplo: `"per_user_limit": -1` significa que não há limite por usuário
- Exemplo: `"global_limit": -1` significa que não há limite global de uso

#### `redemptions` (Resgates/Validações no balcão)

```json
{
  "tenant_id": "knn_ma_sjr_cohatrac",
  "benefit_id": "benefitDocId",
  "partner_id": "partnerDocId",
  "user_uid": "auth_uid_aluno_ou_func",  // UID do Firebase Auth (tipo determinado via roles)
  "value": 35.90,                       // economia gerada, se aplicável
  "code": "ABCD-1234",                  // quando validation.mode == 'code'
  "user_id": "12345",                    // quando validation.mode == 'id'
  "status": "redeemed|rejected",
  "created_at": 1722556800000
}
```

**Nota sobre user_type:**
O campo `user_type` foi removido pois é **redundante**. O tipo de usuário (student/employee) já pode ser determinado através dos **custom claims** (`roles`) no token JWT do Firebase Authentication:

- `roles: ["student"]` → usuário é aluno
- `roles: ["employee"]` → usuário é funcionário

Esta abordagem elimina duplicação de dados e garante consistência com o sistema de autenticação.

> Outras coleções úteis: `codes` (opcional, se gerar códigos únicos previamente), `notifications`, `metrics_daily` (agregados por dia e por tenant), etc.

---

## 3) Regras de segurança do Firestore

> **Padrão**: checagens por *tenant* + papel (role).
> Na implementação atual (JWT), o *tenant* vem em **`request.auth.token.tenant_id`**.
> Na futura implementação com Identity Platform, o *tenant* virá em **`request.auth.token.firebase.tenant`**.

```rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    function isAuth() { return request.auth != null; }
    function tenant() { return request.auth.token.firebase.tenant; }
    function roles() { return request.auth.token.roles != null ? request.auth.token.roles : []; }
    function hasRole(r) { return isAuth() && r in roles(); }
    function sameTenant() { return isAuth() && resource.data.tenant_id == tenant(); }
    function sameTenantNew() { return isAuth() && request.resource.data.tenant_id == tenant(); }

    // ---- STUDENTS ----
    match /students/{id} {
      allow read: if sameTenant() && (hasRole('admin') ||
        (hasRole('student') && request.auth.uid == resource.data.uid));
      allow create: if sameTenantNew() && hasRole('admin');
      allow update, delete: if sameTenant() && sameTenantNew() && hasRole('admin');
    }

    // ---- EMPLOYEES ----
    match /employees/{id} {
      allow read: if sameTenant() && (hasRole('admin') ||
        (hasRole('employee') && request.auth.uid == resource.data.uid));
      allow create: if sameTenantNew() && hasRole('admin');
      allow update, delete: if sameTenant() && sameTenantNew() && hasRole('admin');
    }

    // ---- PARTNERS ----
    match /partners/{id} {
      allow read: if sameTenant() && (hasRole('admin') || hasRole('student') || hasRole('employee') || hasRole('partner'));
      allow create: if sameTenantNew() && hasRole('admin');
      allow update, delete: if sameTenant() && sameTenantNew() && (
        hasRole('admin') || (hasRole('partner') && request.auth.uid == resource.data.owner_uid)
      );
    }

    // ---- BENEFITS ----
    match /benefits/{id} {
      // leitura condicionada à audiência
      allow read: if sameTenant() && (
        hasRole('admin') || hasRole('partner') ||
        (hasRole('student')  && 'student'  in resource.data.audience) ||
        (hasRole('employee') && 'employee' in resource.data.audience)
      );
      allow create: if sameTenantNew() && (hasRole('admin') || hasRole('partner'));
      allow update, delete: if sameTenant() && sameTenantNew() && (
        hasRole('admin') ||
        (hasRole('partner') && request.auth.uid == get(/databases/$(database)/documents/partners/$(resource.data.partner_id)).data.owner_uid)
      );
    }

    // ---- REDEMPTIONS ----
    match /redemptions/{id} {
      // leitura: admin vê tudo do tenant; parceiro vê seus próprios; usuário vê o que ele resgatou
      allow read: if sameTenant() && (
        hasRole('admin') ||
        (hasRole('partner') && resource.data.partner_id in request.auth.token.partner_ids) ||
        (request.auth.uid == resource.data.user_uid)
      );

      // criação: apenas parceiro do tenant (validação no balcão)
      allow create: if sameTenantNew() && hasRole('partner');

      // atualização/cancelamento (se existir política): admin ou parceiro dono do resgate
      allow update, delete: if sameTenant() && sameTenantNew() && (
        hasRole('admin') ||
        (hasRole('partner') && resource.data.partner_id in request.auth.token.partner_ids)
      );
    }
  }
}
```

> **Dica:** Para evitar *PERMISSION_DENIED* em queries, o **cliente sempre filtra** por `tenant_id` **e** por `audience` adequada ao papel do usuário (ex.: aluno busca `where('audience','array-contains','student')`).

---

## 4) Disciplina de consultas e índices

### 4.1 Sempre filtrar por `tenant_id`

Exemplos (Web v9):

```ts
import { collection, query, where, getDocs } from "firebase/firestore";

const qBenefitsStudent = query(
  collection(db, "benefits"),
  where("tenant_id", "==", TENANT_ID),
  where("audience", "array-contains", "student"),
  where("status", "==", "active")
);

const qPartnerMyBenefits = query(
  collection(db, "benefits"),
  where("tenant_id", "==", TENANT_ID),
  where("partner_id", "==", myPartnerId)
);
```

### 4.2 Índices recomendados

- `benefits(tenant_id, status, valid_to DESC)`
- `benefits(tenant_id, audience, status)` *(para `array-contains` usar índice sugerido pelo console)*
- `redemptions(tenant_id, partner_id, created_at DESC)`
- `redemptions(tenant_id, user_uid, created_at DESC)`
- `students(tenant_id, status)` e `employees(tenant_id, status)`
- `partners(tenant_id, status)`

---

## 5) Backend (FastAPI) — verificação de token e papéis

### 5.1 Verificar ID token e extrair tenant/roles

```python
# src/auth/deps.py
from fastapi import Depends, Header, HTTPException
from firebase_admin import auth as fb_auth

def current_user(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split()
        assert scheme.lower() == "bearer"
        decoded = fb_auth.verify_id_token(token)
        tenant = decoded.get("firebase", {}).get("tenant")
        roles = decoded.get("roles", [])
        uid = decoded["uid"]
        return {"uid": uid, "tenant": tenant, "roles": roles}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 5.2 Atribuir *custom claims* (roles, partner_ids)

```python
# src/auth/admin.py
from firebase_admin import auth

def set_claims(uid: str, tenant_id: str, roles: list[str], partner_ids: list[str] = []):
    claims = {"roles": roles, "tenant_id": tenant_id}
    if partner_ids:
        claims["partner_ids"] = partner_ids
    auth.set_custom_user_claims(uid, claims)
```

### 5.3 Endpoints essenciais

- **/benefits**: criar/editar (admin/partner), listar por `tenant_id` e `audience`.
- **/partners/{id}/redemptions**: criar resgate; valida regras (`per_user_limit`, validade, estoque).
- **/users/me**: retorna `uid`, `tenant`, `roles`.
- **/codes** (opcional): gerar códigos únicos (policy **server-side only**).
- **/admin/users/create-student-temp**: criar aluno com senha temporária (admin only).
- **/admin/users/create-employee-temp**: criar funcionário com senha temporária (admin only).
- **/auth/activate-account**: ativar conta com senha temporária (primeiro acesso).
- **/admin/users/pending-activation**: listar usuários pendentes de ativação (admin only).

### 5.4 Cloud Run + Segredos

- Montar **Service Account** no contêiner (Secret Manager) e exportar:
  - `GOOGLE_APPLICATION_CREDENTIALS=/secrets/fb-admin-key/creds.json`
  - `FIREBASE_PROJECT_ID=knn-benefits`
- *Healthcheck* e *readiness* no FastAPI para *rolling updates* limpos.

---

## 6) Front-end (React + Vite) — bootstrap de tenant e guardas

### 6.1 Bootstrap

```ts
// src/main.tsx
import { setTenantForAuth } from "./auth/tenant";
import { detectTenantFromUrl } from "./tenant/detect";

const t = detectTenantFromUrl(window.location.hostname, window.location.pathname);
setTenantForAuth(t);
```

```ts
// src/tenant/detect.ts
export function detectTenantFromUrl(host: string, path: string): string | null {
  const sub = host.split(".")[0];
  if (sub !== "www" && sub !== "journeyclub") return sub; // subdomínio como tenant
  const m = path.match(/\/t\/([a-z0-9_\-]+)/i);
  return m ? m[1] : null;
}
```

### 6.2 Guarda por papel

```ts
export function canSeeBenefit(userRoles: string[], audience: string[]): boolean {
  if (userRoles.includes("admin") || userRoles.includes("partner")) return true;
  if (userRoles.includes("student") && audience.includes("student")) return true;
  if (userRoles.includes("employee") && audience.includes("employee")) return true;
  return false;
}
```

---

## 7) Fluxos de Benefícios e Resgates

### 7.1 Criação de Benefícios (Parceiro/Admin)

1. Parceiro/Admin preenche título, descrição, **audience** (`["student"]`, `["employee"]` ou ambos).
2. Define *validation*:
   - `mode = "code"` → resgate mediante **código de uso único**;
   - `mode = "id"` → validação por **ID** (o balcão confere pelo Nome Completo).
3. Define limites: `per_user_limit`, `global_limit`, `valid_from/to`.
4. Salva documento em `benefits` com `tenant_id`.

### 7.2 Geração/Validação

- **Códigos únicos (`mode='code'`)**:
  - **Server-side** gera e valida códigos (evita fraude/enumeração).
  - `redemptions` é criado pelo Parceiro ao usar o código (status `redeemed`).
- **ID (`mode='id'`)**:
  - Parceiro informa ID do usuário e benefit; backend checa limites e validade.
  - Parceiro confirma identidade pelo Nome Completo do usuário.
  - Registra `redemptions` e retorna OK/erro.

### 7.3 Histórico e economia

- Cada resgate registra `value` (economia) quando aplicável.
- Dashboards (Admin/Parceiro) usam *queries* por `tenant_id` + filtros.

---

## 8) Métricas e BI

- **Agregados diários** por `tenant_id`: `metrics_daily` com `redeems_count`, `unique_users`, `avg_ticket`, `total_savings`.
- **Replica para PostgreSQL** (ou BigQuery) 1x/dia: exporte coleções principais.
- **Chaves de negócio**: `tenant_id`, `partner_id`, `benefit_id`, `user_uid`, `created_at`.

---

## 9) Testes, seed e ambientes

### 9.1 Usuários de teste por tenant

- `admin@{tenant}.local` → roles `["admin"]`
- `parceiro@{tenant}.local` → roles `["partner"]`, `partner_ids: ["partnerDocId"]`
- `aluno@{tenant}.local` → roles `["student"]`
- `func@{tenant}.local` → roles `["employee"]`

### 9.2 Seed (Admin SDK)

```python
from firebase_admin import firestore

db = firestore.client()
db.collection("partners").add({
  "tenant_id": "knn_ma_sjr_cohatrac",
  "name": "Cine World",
  "owner_uid": "uid_parceiro",
  "status": "active",
})
```

---

## 10) Estratégia de Autenticação

### 10.1 Implementação Atual (Recomendada)

#### Arquitetura JWT + JWKS + Firebase Admin SDK

**Decisão:** Manter a implementação atual de autenticação JWT para o cenário atual.

**Vantagens:**

- Simplicidade de implementação e manutenção
- Controle total sobre o processo de autenticação
- Performance otimizada (sem overhead adicional)
- Custo zero adicional
- Flexibilidade para customizações
- Compatibilidade total com a base de código existente

**Adequada para:**

- Cenário atual: 1 escola (KNN Portal)
- Até 2-5 escolas com crescimento moderado

### 10.2 Migração Futura (Identity Platform)

**Condições para Migração:**

- **5+ escolas:** Migração recomendada
- **10+ escolas:** Migração obrigatória
- Necessidade de recursos avançados de autenticação (MFA, SSO)
- Requisitos de compliance mais rigorosos

**Benefícios da Migração:**

- Gerenciamento centralizado de tenants
- Recursos avançados (MFA, SSO, provedores externos)
- Isolamento completo por tenant
- Escalabilidade automática
- Redução da complexidade de manutenção

**Estratégia de Migração em Fases:**

1. **Fase 1:** Manter JWT atual (implementação estável)
2. **Fase 2:** Implementar Identity Platform em paralelo (ambiente de teste)
3. **Fase 3:** Migração gradual por escola (rollout controlado)
4. **Fase 4:** Descomissionamento da implementação JWT

### 10.3 Critérios de Decisão

**Manter JWT quando:**

- Número de escolas < 5
- Recursos de autenticação básicos são suficientes
- Equipe tem controle total sobre o sistema
- Orçamento limitado para ferramentas adicionais

**Migrar para Identity Platform quando:**

- Número de escolas >= 5
- Necessidade de recursos avançados
- Requisitos de compliance rigorosos
- Equipe precisa focar no core business

---

## 11) Recomendações de Implementação

### 11.1 Fase 1: Adaptação Gradual

#### 1. Manter a autenticação JWT atual ✅

- Implementação já estável e funcional
- Adequada para o cenário atual (1 escola)
- Performance otimizada sem overhead adicional

#### 2. Implementar novos campos no modelo de dados

**Campos `audience` e `validation` nos benefícios:**

```json
{
  "tenant_id": "knn_ma_sjr_cohatrac",
  "partner_id": "partnerDocId",
  "title": "Desconto em Livros",
  "description": "20% de desconto em todos os livros",
  "audience": ["student", "employee"],  // Novo campo: público-alvo
  "validation": {                        // Novo campo: regras de validação
    "mode": "code",                     // "code" ou "cpf"
    "per_user_limit": 2,               // Limite por usuário (-1 = ilimitado)
    "global_limit": 1000,              // Limite global (-1 = ilimitado)
    "valid_from": 1722470400000,       // Data início
    "valid_to": 1730246400000          // Data fim
  },
  "status": "active",
  "created_at": 1719868800000,
  "updated_at": 1719868800000
}
```

#### 3. Atualizar regras de Firestore

**Adicionar validações para os novos campos:**

```rules
// Validação de audience nos benefits
allow read: if sameTenant() && (
  hasRole('admin') || hasRole('partner') ||
  (hasRole('student') && 'student' in resource.data.audience) ||
  (hasRole('employee') && 'employee' in resource.data.audience)
);

// Validação de campos obrigatórios na criação
allow create: if sameTenantNew() &&
  request.resource.data.keys().hasAll(['audience', 'validation']) &&
  request.resource.data.audience is list &&
  request.resource.data.validation.keys().hasAll(['mode', 'per_user_limit']);
```

#### 4. Adicionar novos endpoints para benefícios

**Endpoints específicos para o novo modelo:**

- `GET /v1/benefits?audience=student` - Filtrar por público-alvo
- `POST /v1/benefits/{id}/validate` - Validar código/ID
- `GET /v1/benefits/{id}/usage` - Estatísticas de uso
- `POST /v1/codes/generate` - Gerar códigos únicos (server-side)

### 11.2 Fase 2: Melhorias de Segurança

#### 1. Implementar custom claims mais granulares

**Claims específicos por funcionalidade:**

```python
# Exemplo de claims granulares
claims = {
    "roles": ["partner"],
    "tenant_id": "knn_ma_sjr_cohatrac",
    "partner_ids": ["partner123"],           # Parceiros que pode gerenciar
    "permissions": [                          # Permissões específicas
        "benefits:create",
        "benefits:update",
        "redemptions:validate"
    ],
    "rate_limit_tier": "premium"             # Tier de rate limiting
}
```

#### 2. Adicionar auditoria detalhada

**Log estruturado para todas as operações:**

```python
# Exemplo de log de auditoria
audit_log = {
    "timestamp": datetime.utcnow().isoformat(),
    "tenant_id": "knn_ma_sjr_cohatrac",
    "user_uid": "user123",
    "user_role": "partner",
    "action": "benefit_create",
    "resource_id": "benefit456",
    "ip_address": request.client.host,
    "user_agent": request.headers.get("user-agent"),
    "success": True,
    "details": {
        "audience": ["student"],
        "validation_mode": "code"
    }
}
```

#### 3. Otimizar índices conforme sugerido

**Índices específicos para os novos campos:**

```javascript
// Índices recomendados para Firestore
[
  // Para filtros por audience
  {
    "collectionGroup": "benefits",
    "fields": [
      {"fieldPath": "tenant_id", "order": "ASCENDING"},
      {"fieldPath": "audience", "arrayConfig": "CONTAINS"},
      {"fieldPath": "status", "order": "ASCENDING"},
      {"fieldPath": "created_at", "order": "DESCENDING"}
    ]
  },
  // Para validação de códigos
  {
    "collectionGroup": "redemptions",
    "fields": [
      {"fieldPath": "tenant_id", "order": "ASCENDING"},
      {"fieldPath": "code", "order": "ASCENDING"},
      {"fieldPath": "status", "order": "ASCENDING"}
    ]
  }
]
```

#### 4. Implementar rate limiting por tenant

**Rate limiting diferenciado por tenant:**

```python
# Rate limiting por tenant
RATE_LIMITS = {
    "default": "100/minute",
    "premium_tenants": {
        "knn_ma_sjr_cohatrac": "500/minute",  # Tenant premium
        "knn_imperatriz": "200/minute"
    },
    "endpoints": {
        "/v1/codes/generate": "10/minute",     # Limite específico
        "/v1/benefits/validate": "50/minute"
    }
}
```

### 11.3 Benefícios das Implementações

**Fase 1 - Adaptação Gradual:**

- ✅ Compatibilidade com sistema atual
- ✅ Implementação incremental sem breaking changes
- ✅ Melhoria na flexibilidade dos benefícios
- ✅ Preparação para escalabilidade futura

**Fase 2 - Melhorias de Segurança:**

- 🔒 Controle de acesso mais granular
- 📊 Auditoria completa para compliance
- ⚡ Performance otimizada com índices específicos
- 🛡️ Proteção contra abuso com rate limiting inteligente

---

## 12) Boas práticas e "pontos de corte"

- **Sempre** filtrar consultas por `tenant_id`; falhas viram `PERMISSION_DENIED`.
- Imutabilidade de `tenant_id` nas regras (comparar `resource` vs `request.resource`).
- Não gerar **códigos** no cliente: somente servidor/Cloud Functions.
- Índices com `tenant_id` **primeiro**; leia o plano de execução sugerido pelo console.
- Logs com `tenant`/`role` em cada endpoint (auditoria).
- **Superadmin**: `auth.tenantId = null` no login; `custom claim` `superadmin: true` limita acesso a *routes* administrativas.

---

## 13) Apêndice A — Tabela de papéis e permissões (resumo)

| Entidade      | Ler                              | Criar                         | Atualizar/Excluir                                 |
|---------------|----------------------------------|-------------------------------|---------------------------------------------------|
| **students**  | admin; aluno (próprio)           | admin                         | admin                                             |
| **employees** | admin; funcionário (próprio)     | admin                         | admin                                             |
| **partners**  | admin; aluno; func; parceiro     | admin                         | admin; parceiro (se próprio `owner_uid`)          |
| **benefits**  | admin; parceiro; aluno/func conforme `audience` | admin; parceiro | admin; parceiro (do próprio `partner_id`)         |
| **redemptions** | admin; parceiro (seus); usuário (próprios) | parceiro | admin; parceiro (seus)                             |
| **temp_passwords** | admin (todos do tenant)      | admin                         | admin; sistema (expiração automática)            |
| **user_activation** | admin; usuário (próprio)    | admin                         | usuário (ativação própria); admin                |

---

## 14) Apêndice B — Checklist de entrega (MVP)

1. **Front**: `setTenantForAuth()` no bootstrap; guarda de papéis; filtros por `tenant_id` e `audience`.
2. **Rules**: publicadas e testadas com usuários de cada papel.
3. **Backend**: middleware de token, endpoints de benefícios e resgates; geração de códigos server-side (se aplicável).
4. **Índices**: criados para consultas principais.
5. **Parceiro**: tela de validação (ID/código) e relatórios.
6. **Admin**: CRUD de usuários, parceiros, benefícios; painel com KPIs.
7. **Logs/Auditoria**: *request id*, `tenant`, `uid`, `role` em cada chamada.

---

## 15) Apêndice C — Exemplos de consultas

```ts
// Benefícios visíveis para ALUNO
query(collection(db,"benefits"),
  where("tenant_id","==",TENANT_ID),
  where("audience","array-contains","student"),
  where("status","==","active"));

// Resgates do PARCEIRO no mês
query(collection(db,"redemptions"),
  where("tenant_id","==",TENANT_ID),
  where("partner_id","==",myPartnerId),
  where("created_at",">=", monthStartTs));
```

---

**Fim do documento.**
