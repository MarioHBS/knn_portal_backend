# Relatório Técnico: Algoritmos de Geração de IDs Personalizados

## Visão Geral

Este documento fornece informações técnicas sobre os algoritmos de geração de IDs personalizados implementados no backend, destinado à equipe de Frontend para integração adequada.

## Estrutura dos IDs Gerados

### Formato Geral

Todos os IDs seguem o padrão: `PREFIXO_CODIGO_INTERCALADO_SUFIXO`

### Tipos de Entidades

#### 1. Alunos (Students)

- **Prefixo**: `STD_`
- **Algoritmo**: Intercalação de iniciais do nome + dígitos do CEP + dígitos do celular + dígitos do email
- **Sufixos por Curso**:
  - KIDS 1, KIDS 2, KIDS 3 → `_K1`, `_K2`, `_K3`
  - TEENS 1, TEENS 2, TEENS 3 → `_T1`, `_T2`, `_T3`
  - ADVANCED 1, ADVANCED 2, ADVANCED 3 → `_A1`, `_A2`, `_A3`
  - CONVERSATION → `_CV`
  - BUSINESS → `_BZ`
  - Outros → `_OT`

**Exemplo**: João Silva Santos, KIDS 1, CEP 12345-678, Celular (11) 99999-9999

→ `STD_J6S7S899_K1`

#### 2. Funcionários (Employees)

- **Prefixo**: `EMP_`
- **Algoritmo**: Intercalação de iniciais do nome + dígitos do CEP + dígitos do telefone
- **Sufixos por Cargo**:
  - PROFESSORA, PROFESSOR → `_PR`
  - CDA → `_CDA`
  - ADM. FINANCEIRO → `_AF`
  - COORDENADORA → `_CO`
  - Outros → `_OT`

**Exemplo**: Carlos Eduardo, PROFESSORA, CEP 11111-222, Telefone (11) 55555-5555

→ `EMP_C2E22555_PR`

#### 3. Parceiros (Partners)

- **Prefixo**: `PTN_`
- **Algoritmo**: Intercalação de iniciais do trade_name + dígitos do CNPJ
- **Sufixos por Categoria**:
  - TECNOLOGIA → `_TEC`
  - SAÚDE → `_SAU`
  - EDUCAÇÃO → `_EDU`
  - ALIMENTAÇÃO → `_ALI`
  - VAREJO → `_VAR`
  - SERVIÇOS → `_SER`
  - Outros → `_OT`

**Exemplo**: Tech Solutions, TECNOLOGIA, CNPJ 12.345.678/0001-90

→ `PTN_T4S5678_TEC`

## Integração com Frontend

### 1. Endpoints da API

Os IDs são gerados automaticamente pelo backend nos seguintes endpoints:

```http
POST /api/students
POST /api/employees  
POST /api/partners
`$language

### 2. Campos Obrigatórios por Entidade

#### Para Alunos

```json
{
  "nome_aluno": "string (obrigatório)",
  "curso": "string (obrigatório)",
  "cep": "string (formato: XXXXX-XXX)",
  "celular": "string (formato brasileiro)",
  "email": "string (opcional)"
}
`$language

#### Para Funcionários

```json
{
  "name": "string (obrigatório)",
  "department": "string (obrigatório)",
  "cep": "string (formato: XXXXX-XXX)",
  "telefone": "string (formato brasileiro)"
}
`$language

#### Para Parceiros

```json
{
  "trade_name": "string (obrigatório)",
  "category": "string (obrigatório)",
  "cnpj": "string (formato: XX.XXX.XXX/XXXX-XX)"
}
`$language

### 3. Comportamento da API

- **Geração Automática**: Se o campo `id` não for fornecido, será gerado automaticamente
- **Preservação**: Se o campo `id` for fornecido, será mantido (não sobrescrito)
- **Fallback**: Em caso de erro na geração, utiliza UUID4 como fallback

### 4. Validação no Frontend

#### Formato de ID Válido

```javascript
// Regex para validação de IDs gerados
const ID_PATTERN = /^(STD|EMP|PTN)_[A-Z0-9]+_(K[1-3]|T[1-3]|A[1-3]|CV|BZ|PR|CDA|AF|CO|TEC|SAU|EDU|ALI|VAR|SER|OT)$/;

function isValidCustomID(id) {
  return ID_PATTERN.test(id);
}
`$language

#### Validação de Campos

```javascript
// Validação de CEP brasileiro
function isValidCEP(cep) {
  return /^\d{5}-\d{3}$/.test(cep);
}

// Validação de telefone brasileiro
function isValidPhone(phone) {
  return /^\(\d{2}\)\s\d{4,5}-\d{4}$/.test(phone);
}

// Validação de CNPJ
function isValidCNPJ(cnpj) {
  return /^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$/.test(cnpj);
}
`$language

### 5. Exemplos de Requisições

#### Criando um Aluno

```javascript
const studentData = {
  nome_aluno: "Maria Silva Santos",
  curso: "TEENS 2",
  cep: "01234-567",
  celular: "(11) 98765-4321",
  email: "maria@escola.com",
  tenant_id: "escola_abc",
  cpf_hash: "hash_do_cpf"
};

fetch('/api/students', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(studentData)
})
.then(response => response.json())
.then(data => {
  console.log('ID gerado:', data.id); // Ex: STD_M1S2S4321_T2
});
`$language

#### Criando um Funcionário

```javascript
const employeeData = {
  name: "João Carlos Silva",
  department: "PROFESSOR",
  cep: "12345-678",
  telefone: "(21) 99999-8888",
  email: "joao@escola.com",
  tenant_id: "escola_abc"
};

fetch('/api/employees', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(employeeData)
})
.then(response => response.json())
.then(data => {
  console.log('ID gerado:', data.id); // Ex: EMP_J5C6S8888_PR
});
`$language

#### Criando um Parceiro

```javascript
const partnerData = {
  trade_name: "Tecnologia & Inovação Ltda",
  category: "TECNOLOGIA",
  cnpj: "12.345.678/0001-90",
  tenant_id: "escola_abc"
};

fetch('/api/partners', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(partnerData)
})
.then(response => response.json())
.then(data => {
  console.log('ID gerado:', data.id); // Ex: PTN_T6I7678_TEC
});
`$language

### 6. Tratamento de Erros

```javascript
function handleAPIResponse(response) {
  if (!response.ok) {
    throw new Error(`Erro ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

// Uso com tratamento de erro
fetch('/api/students', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(studentData)
})
.then(handleAPIResponse)
.then(data => {
  if (isValidCustomID(data.id)) {
    console.log('ID válido gerado:', data.id);
  } else {
    console.warn('ID gerado não segue o padrão esperado:', data.id);
  }
})
.catch(error => {
  console.error('Erro ao criar estudante:', error);
});
`$language

### 7. Considerações Importantes

1. **Unicidade**: Os IDs gerados são únicos dentro do contexto de cada tenant
2. **Determinismo**: Dados idênticos sempre geram o mesmo ID
3. **Fallback**: Em caso de falha, o sistema usa UUID4
4. **Validação**: Sempre valide os formatos de entrada no frontend
5. **Tratamento**: Implemente tratamento adequado para casos de erro

### 8. Testes de Validação

O backend possui 26 testes unitários que validam:

- Geração correta de IDs para cada tipo de entidade
- Mapeamento correto de cursos, cargos e categorias
- Tratamento de casos extremos (nomes acentuados, dados incompletos)
- Validação de formatos de entrada
- Intercalação correta de iniciais e dígitos

## Conclusão

Este sistema de IDs personalizados oferece identificadores únicos, legíveis e estruturados que facilitam a identificação visual do tipo de entidade e suas características principais. A implementação no frontend deve seguir as diretrizes de validação e tratamento de erros apresentadas neste documento.

Para dúvidas ou suporte técnico, consulte a documentação da API ou entre em contato com a equipe de backend.
