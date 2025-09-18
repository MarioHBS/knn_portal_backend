# Configuração do Firebase - Portal de Benefícios KNN

## Visão Geral

Este documento explica como configurar o Firebase para o Portal de Benefícios KNN. O projeto utiliza Firebase/Firestore como banco de dados principal.

## Status Atual

❌ **Firebase NÃO configurado** - Credenciais pendentes

## Configurações Necessárias

As seguintes variáveis de ambiente devem ser configuradas no arquivo `.env`:

```env
# Configurações do Firebase
FB_API_KEY=your-api-key-here
FB_AUTH_DOMAIN=your-project.firebaseapp.com
FB_PROJECT_ID=your-project-id
FB_STORAGE_BUCKET=your-project.appspot.com
FB_MESSAGING_SENDER_ID=123456789
FB_APP_ID=your-app-id
FB_MEASUREMENT_ID=your-measurement-id
```

## Como Obter as Credenciais

### 1. Acesse o Console do Firebase

1. Vá para [Firebase Console](https://console.firebase.google.com/)
2. Faça login com sua conta Google
3. Selecione o projeto `knn-portal-dev` (ou crie um novo)

### 2. Obtenha as Configurações do Projeto

1. No console do Firebase, clique no ícone de engrenagem (⚙️) no menu lateral
2. Selecione "Configurações do projeto"
3. Role para baixo até a seção "Seus aplicativos"
4. Se não houver um app web, clique em "Adicionar app" e selecione "Web" (</>)
5. Registre o app com o nome "KNN Portal Backend"
6. Copie as configurações mostradas

### 3. Configure as Variáveis de Ambiente

Substitua os valores no arquivo `.env`:

```bash
# Exemplo de configuração real (substitua pelos seus valores)
VITE_FB_API_KEY=AIzaSyC...
VITE_FB_AUTH_DOMAIN=knn-portal-dev.firebaseapp.com
VITE_FB_PROJECT_ID=knn-portal-dev
VITE_FB_STORAGE_BUCKET=knn-portal-dev.appspot.com
VITE_FB_MESSAGING_SENDER_ID=123456789012
VITE_FB_APP_ID=1:123456789012:web:abcdef123456
VITE_FB_MEAS_ID=G-XXXXXXXXXX
```

## Configuração do Firestore

### 1. Ativar o Firestore

1. No console do Firebase, vá para "Firestore Database"
2. Clique em "Criar banco de dados"
3. Escolha "Iniciar no modo de teste" (para desenvolvimento)
4. Selecione uma localização (recomendado: `southamerica-east1` para Brasil)

### 2. Configurar Regras de Segurança (Desenvolvimento)

Para desenvolvimento, use regras permissivas:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

⚠️ **IMPORTANTE**: Em produção, implemente regras de segurança adequadas!

### 3. Estrutura das Coleções

O projeto utiliza as seguintes coleções:

- `students` - Dados dos alunos
- `partners` - Dados dos parceiros comerciais
- `promotions` - Promoções disponíveis
- `validation_codes` - Códigos de validação
- `redemptions` - Histórico de resgates

## Autenticação de Serviço (Produção)

Para ambiente de produção, configure a autenticação de serviço:

### 1. Criar Conta de Serviço

1. Vá para [Google Cloud Console](https://console.cloud.google.com/)
2. Selecione o projeto Firebase
3. Vá para "IAM e administrador" > "Contas de serviço"
4. Clique em "Criar conta de serviço"
5. Preencha os detalhes e conceda o papel "Firebase Admin SDK Administrator Service Agent"
6. Crie e baixe a chave JSON

### 2. Configurar Credenciais

```bash
# Definir variável de ambiente apontando para o arquivo JSON
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

Ou no arquivo `.env`:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## Testes

### Verificar Configuração

Execute o script de verificação:

```bash
python firebase_config.py
```

### Testar Conexão

Execute o teste de conexão:

```bash
python test_firebase_connection.py
```

## Solução de Problemas

### Erro: "Cliente Firestore não foi inicializado"

**Possíveis causas:**

- Credenciais não configuradas
- Projeto Firebase não existe
- Problemas de rede
- Regras de segurança muito restritivas

**Soluções:**

1. Verifique se todas as variáveis de ambiente estão definidas
2. Confirme se o projeto Firebase existe e está ativo
3. Verifique as regras de segurança do Firestore
4. Teste a conectividade com a internet

### Erro: "The default Firebase app already exists"

**Causa:** Múltiplas inicializações do Firebase

**Solução:** Reinicie o servidor/aplicação

### Erro de Permissões

**Causa:** Regras de segurança restritivas

**Solução:** Ajuste as regras do Firestore ou configure autenticação adequada

## Próximos Passos

1. ✅ Configurar variáveis de ambiente no `.env`
2. ⏳ Obter credenciais reais do Firebase Console
3. ⏳ Testar conexão com `python test_firebase_connection.py`
4. ⏳ Configurar regras de segurança adequadas
5. ⏳ Implementar dados de seed para desenvolvimento

## Recursos Úteis

- [Documentação Firebase](https://firebase.google.com/docs)
- [Firestore Python SDK](https://firebase.google.com/docs/firestore/quickstart#python)
- [Firebase Console](https://console.firebase.google.com/)
- [Google Cloud Console](https://console.cloud.google.com/)

---

**Última atualização:** Janeiro 2025
**Status:** Configuração inicial criada - Aguardando credenciais reais