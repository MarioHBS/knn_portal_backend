# Documentação Frontend - Portal de Benefícios KNN

## 📋 Visão Geral

Esta pasta contém toda a documentação necessária para o **Frontend** integrar com a API do Portal de Benefícios KNN. Os documentos foram organizados para fornecer apenas as informações relevantes para o desenvolvimento Frontend, sem expor detalhes internos dos algoritmos do Backend.

## 📁 Arquivos Disponíveis

### 1. 🔌 [api_endpoints.md](./api_endpoints.md)

**Especificação completa da API**

- Endpoints para Estudantes, Funcionários e Parceiros
- Exemplos de requisição e resposta
- Códigos de status HTTP
- Headers obrigatórios
- Tratamento de erros
- Rate limiting e paginação

### 2. ✅ [validacoes_frontend.md](./validacoes_frontend.md)

**Validações que devem ser implementadas no Frontend**

- Funções JavaScript para validação de campos
- Máscaras de entrada (telefone, CEP, CNPJ)
- Validações específicas por tipo de entidade
- Exemplos de uso completos

### 3. ⚛️ [exemplo_componente_react.md](./exemplo_componente_react.md)

**Componente React completo para cadastro de estudante**

- Código React funcional pronto para uso
- Integração com API
- Validações em tempo real
- Tratamento de erros
- Estilos CSS incluídos

## 🚀 Como Usar

### Passo 1: Configurar API

1. Leia o arquivo `api_endpoints.md`
2. Configure a URL base da API
3. Implemente autenticação JWT
4. Configure headers obrigatórios

### Passo 2: Implementar Validações

1. Copie as funções do arquivo `validacoes_frontend.md`
2. Adapte para seu framework (React, Vue, Angular)
3. Implemente máscaras de entrada
4. Configure mensagens de erro

### Passo 3: Criar Componentes

1. Use o exemplo React como base
2. Adapte para seu design system
3. Implemente componentes para Funcionários e Parceiros
4. Teste todas as validações

## 🎯 Pontos Importantes

### ✅ O que o Frontend DEVE fazer

- **Validar dados** antes de enviar para API
- **Aplicar máscaras** nos campos de entrada
- **Tratar erros** da API adequadamente
- **Respeitar rate limits** (100 req/min)
- **Usar HTTPS** em produção
- **Incluir headers obrigatórios** em todas as requisições

### ❌ O que o Frontend NÃO precisa fazer

- **Gerar IDs** - isso é feito automaticamente pelo Backend
- **Conhecer algoritmos** de geração de IDs
- **Implementar lógica** de mapeamento de sufixos
- **Validar unicidade** de IDs - o Backend garante isso

## 🔧 Configuração Rápida

### Variáveis de Ambiente

```env

# .env

REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_TENANT_ID=sua_escola_id
`$language

### Headers Padrão

```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`,
  'X-Tenant-ID': process.env.REACT_APP_TENANT_ID
};
`$language

### Exemplo de Requisição

```javascript
const response = await fetch('/api/v1/students', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    nome: 'João Silva',
    email: 'joao@email.com',
    cep: '12345-678',
    curso: 'Engenharia de Software',
    data_nascimento: '2000-01-01'
  })
});

const estudante = await response.json();
console.log('ID gerado:', estudante.id); // Ex: STD_J6S7S899_K1
`$language

## 📊 Formatos de ID Gerados

O Backend gera automaticamente IDs no seguinte formato:

| Tipo | Formato | Exemplo |
|------|---------|----------|
| **Estudante** | `STD_<codigo>_<sufixo>` | `STD_J6S7S899_K1` |
| **Funcionário** | `EMP_<codigo>_<sufixo>` | `EMP_C2E22555_PR` |
| **Parceiro** | `PTN_<codigo>_<sufixo>` | `PTN_T4S5678_TEC` |

> **Nota:** O Frontend não precisa entender como esses IDs são gerados, apenas consumi-los.

## 🐛 Troubleshooting

### Erro 400 - Validation Error

- Verifique se todos os campos obrigatórios estão preenchidos
- Valide formatos (email, CEP, telefone, CNPJ)
- Confirme se curso/cargo/categoria existem nas listas válidas

### Erro 401 - Unauthorized

- Verifique se o token JWT está válido
- Confirme se o header Authorization está correto
- Verifique se o token não expirou

### Erro 429 - Rate Limit

- Implemente retry com backoff exponencial
- Monitore quantidade de requisições por minuto
- Use debounce em campos de busca

## 📞 Suporte

Para dúvidas sobre a integração:

1. Consulte primeiro esta documentação
2. Verifique os exemplos de código fornecidos
3. Teste em ambiente de desenvolvimento
4. Entre em contato com a equipe Backend se necessário

---

**Última atualização:** Janeiro 2025
**Versão da API:** v1
**Status:** Pronto para produção ✅
