# Comparação dos Endpoints de Parceiros

Este documento detalha as diferenças entre os endpoints `/v1/student/partners` e `/v1/employee/partners`, especificando parâmetros, comportamentos e casos de uso recomendados.

## Visão Geral

Ambos os endpoints compartilham a mesma lógica base através do `PartnersService`, mas possuem configurações específicas para atender às necessidades de cada tipo de usuário.

## Endpoints Disponíveis

### `/v1/student/partners`

- **Método**: GET
- **Autenticação**: Token JWT com role `student`
- **Função de validação**: `validate_student_role`

### `/v1/employee/partners`

- **Método**: GET
- **Autenticação**: Token JWT com role `employee`
- **Função de validação**: `validate_employee_role`

## Parâmetros da Requisição

### Parâmetros Comuns

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|---------|-----------|
| `cat` | string | Não | null | Filtro por categoria do parceiro |
| `limit` | integer | Não | 20 | Número máximo de itens por página (1-100) |
| `offset` | integer | Não | 0 | Offset para paginação (≥0) |

### Parâmetros Específicos

#### Student Endpoint

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|---------|-----------|
| `ord` | string | Não | null | Ordenação dos resultados (ignorado na implementação atual) |

**Valores aceitos para `ord`**: `name_asc`, `name_desc`, `category_asc`, `category_desc`

#### Employee Endpoint

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|---------|-----------|
| `ord` | string | Não | "name" | Ordenação dos resultados |

**Valores aceitos para `ord`**: `name`, `category`

## Diferenças Comportamentais

### 1. Ordenação

#### Student Endpoint - Ordenação

- **Comportamento**: Ordenação **desabilitada**
- **Motivo**: Evitar necessidade de índices complexos no Firestore
- **Configuração**: `enable_ordering=False`
- **Resultado**: Parceiros retornados sem ordenação específica

#### Employee Endpoint - Ordenação

- **Comportamento**: Ordenação **habilitada**
- **Motivo**: Funcionários precisam de dados organizados para operações
- **Configuração**: `enable_ordering=True`
- **Resultado**: Parceiros ordenados conforme parâmetro `ord`

### 2. Circuit Breaker

#### Configuração Comum

- **Comportamento**: Circuit breaker **habilitado**
- **Configuração**: `use_circuit_breaker=True`
- **Benefício**: Alta disponibilidade com fallback para PostgreSQL

### 3. Filtros

#### Configuração de Filtros

- **Filtro base**: Apenas parceiros ativos (`active=true`)
- **Filtro opcional**: Categoria (`cat` parameter)
- **Tenant**: Automaticamente filtrado pelo tenant do usuário

## Estrutura da Resposta

### Formato Comum

```json
{
  "data": [
    {
      "id": "string",
      "trade_name": "string",
      "category": "string",
      "active": true,
      // ... outros campos do parceiro
    }
  ]
}
`$language

### Características da Resposta

- **Tipo**: `PartnerListResponse`
- **Campo principal**: `data` (array de parceiros)
- **Paginação**: Controlada pelos parâmetros `limit` e `offset`
- **Filtros aplicados**: Apenas parceiros ativos do tenant do usuário

## Casos de Uso Recomendados

### Student Endpoint (`/v1/student/partners`)

#### Cenários Ideais

- **Listagem simples**: Estudantes navegando pelos parceiros disponíveis
- **Busca por categoria**: Filtrar parceiros por tipo de benefício
- **Performance otimizada**: Quando ordenação não é crítica

#### Limitações

- Sem ordenação personalizada
- Focado em simplicidade e performance

#### Exemplo de Uso

```bash

# Listar todos os parceiros

GET /v1/student/partners

# Filtrar por categoria

GET /v1/student/partners?cat=alimentacao

# Paginação

GET /v1/student/partners?limit=10&offset=20
`$language

### Employee Endpoint (`/v1/employee/partners`)

#### Cenários Ideais

- **Operações administrativas**: Funcionários gerenciando parceiros
- **Relatórios organizados**: Dados ordenados para análise
- **Interface de gestão**: Quando ordenação é importante para UX

#### Vantagens

- Ordenação flexível por nome ou categoria
- Dados estruturados para operações internas

#### Exemplo de Uso

```bash

# Listar parceiros ordenados por nome

GET /v1/employee/partners?ord=name

# Filtrar e ordenar por categoria

GET /v1/employee/partners?cat=tecnologia&ord=category

# Paginação com ordenação

GET /v1/employee/partners?ord=name&limit=50&offset=0
`$language

## Limitações Conhecidas

### Student Endpoint

1. **Ordenação desabilitada**: Não é possível ordenar os resultados
2. **Performance vs. Funcionalidade**: Prioriza velocidade sobre organização
3. **Índices Firestore**: Evita necessidade de índices compostos

### Employee Endpoint

1. **Dependência de índices**: Pode requerer índices no Firestore para ordenação
2. **Complexidade adicional**: Mais processamento para ordenação

### Limitações Comuns

1. **Apenas parceiros ativos**: Não é possível visualizar parceiros inativos
2. **Filtro de tenant**: Limitado ao tenant do usuário autenticado
3. **Paginação simples**: Offset-based, não cursor-based

## Considerações de Performance

### Student Endpoint

- **Otimizado para velocidade**: Sem ordenação reduz latência
- **Menor uso de recursos**: Consultas mais simples
- **Escalabilidade**: Melhor performance com grandes volumes

### Employee Endpoint

- **Funcionalidade completa**: Ordenação pode impactar performance
- **Uso de índices**: Requer índices adequados no banco
- **Trade-off**: Funcionalidade vs. velocidade

## Monitoramento e Logs

### Logs Comuns

- Número de parceiros retornados
- Tenant e role do usuário
- Parâmetros da consulta
- Tempo de resposta

### Métricas Recomendadas

- Taxa de sucesso por endpoint
- Latência média por role
- Uso de filtros e ordenação
- Eficácia do circuit breaker

## Migração e Compatibilidade

### Mudanças Implementadas

- **Lógica unificada**: Ambos endpoints usam `PartnersService`
- **Circuit breaker**: Adicionado ao endpoint de student
- **Mantida compatibilidade**: APIs permanecem inalteradas

### Impacto nas Aplicações Cliente

- **Nenhuma mudança necessária**: APIs mantêm contratos existentes
- **Melhoria de confiabilidade**: Circuit breaker aumenta disponibilidade
- **Performance**: Possível melhoria na consistência de resposta

## Recomendações de Desenvolvimento

### Para Novos Recursos

1. **Use o PartnersService**: Evite duplicar lógica
2. **Configure adequadamente**: Ajuste `enable_ordering` e `use_circuit_breaker`
3. **Teste ambos cenários**: Com e sem ordenação

### Para Manutenção

1. **Monitore performance**: Especialmente ordenação no employee endpoint
2. **Atualize testes**: Use os testes compartilhados como base
3. **Documente mudanças**: Mantenha esta documentação atualizada

## Conclusão

Os endpoints foram refatorados para compartilhar lógica comum mantendo suas características específicas. O endpoint de student prioriza performance e simplicidade, enquanto o de employee oferece funcionalidades completas para operações administrativas. Ambos se beneficiam do circuit breaker para maior confiabilidade.
