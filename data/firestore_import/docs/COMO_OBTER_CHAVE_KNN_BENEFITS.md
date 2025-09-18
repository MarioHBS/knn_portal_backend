# Como Obter a Chave de Conta de Serviço para 'knn-benefits'

Este guia explica como obter uma chave de conta de serviço válida para o projeto `knn-benefits` no Google Cloud Platform.

## Situação Atual

O projeto **KNNBenefits** possui **dois bancos Firestore distintos**:

### Banco (default)

- **Database ID**: `(default)`
- **Localização**: nam5
- **Status**: Configurado para importação

### Banco knn-benefits

- **Database ID**: `knn-benefits`
- **Localização**: southamerica-east1
- **Status**: Configurado para importação

Este guia serve como referência para configurar chaves de serviço que tenham acesso a ambos os bancos.

## Passos para Obter Nova Chave

### 1. Acessar o Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Faça login com sua conta Google
3. Selecione o projeto `knn-benefits` no seletor de projetos

### 2. Navegar para Contas de Serviço

1. No menu lateral, vá para **IAM & Admin** > **Service Accounts**
2. Ou use a URL direta: `https://console.cloud.google.com/iam-admin/serviceaccounts?project=knn-benefits`

### 3. Criar ou Usar Conta de Serviço Existente

#### Opção A: Usar Conta Existente
1. Procure por uma conta de serviço existente (ex: `firebase-adminsdk-xxxxx@knn-benefits.iam.gserviceaccount.com`)
2. Clique nos três pontos (⋮) à direita da conta
3. Selecione **Manage keys**

#### Opção B: Criar Nova Conta
1. Clique em **+ CREATE SERVICE ACCOUNT**
2. Preencha:
   - **Service account name**: `firestore-admin`
   - **Service account ID**: `firestore-admin`
   - **Description**: `Conta para administração do Firestore`
3. Clique em **CREATE AND CONTINUE**

### 4. Configurar Permissões

A conta de serviço precisa das seguintes permissões:

#### Papéis Necessários:
- **Cloud Datastore User** (`roles/datastore.user`)
- **Firebase Admin** (`roles/firebase.admin`)
- **Service Account Token Creator** (`roles/iam.serviceAccountTokenCreator`)

#### Para Adicionar Papéis:
1. Na seção **Grant this service account access to project**
2. Clique em **Select a role**
3. Adicione cada papel listado acima
4. Clique em **CONTINUE** e depois **DONE**

### 5. Gerar Chave JSON

1. Na lista de contas de serviço, clique na conta criada/selecionada
2. Vá para a aba **KEYS**
3. Clique em **ADD KEY** > **Create new key**
4. Selecione **JSON** como tipo
5. Clique em **CREATE**
6. O arquivo JSON será baixado automaticamente

### 6. Substituir Chave Atual

1. Renomeie o arquivo baixado para `default-service-account-key.json`
2. Substitua o arquivo atual em:
   ```
   p:\ProjectsWEB\PRODUCAO\knn_portal_backend\data\firestore_import\default-service-account-key.json
   ```

### 7. Testar Nova Chave

Execute o script de teste para verificar se a nova chave funciona:

```bash
cd data/firestore_import
python list_firestore_databases.py
```

## Verificações Adicionais

### Verificar Status do Projeto
1. Confirme que o projeto `knn-benefits` está ativo
2. Verifique se o Firestore está habilitado no projeto
3. Confirme que não há restrições de API ativas

### Verificar APIs Habilitadas
Certifique-se de que as seguintes APIs estão habilitadas:
- Cloud Firestore API
- Firebase Admin SDK API
- Identity and Access Management (IAM) API

### Comandos para Habilitar APIs (via gcloud CLI)
```bash
gcloud services enable firestore.googleapis.com --project=knn-benefits
gcloud services enable firebase.googleapis.com --project=knn-benefits
gcloud services enable iam.googleapis.com --project=knn-benefits
```

## Solução de Problemas

### Erro 403 Persiste
- Verifique se você tem permissões de administrador no projeto
- Confirme que a conta de serviço foi criada no projeto correto
- Aguarde alguns minutos para propagação das permissões

### Erro de Projeto Não Encontrado
- Confirme o ID exato do projeto
- Verifique se você tem acesso ao projeto
- Confirme que o projeto não foi excluído ou suspenso

### Erro de API Não Habilitada
- Habilite as APIs necessárias no Console ou via gcloud CLI
- Aguarde alguns minutos para ativação

## Contatos e Suporte

Se os problemas persistirem:
1. Verifique com o administrador do projeto Google Cloud
2. Consulte a documentação oficial do Firebase
3. Verifique logs de auditoria no Google Cloud Console

## Segurança

⚠️ **Importante**:
- Nunca compartilhe arquivos de chave de conta de serviço
- Mantenha as chaves em local seguro
- Rotacione as chaves periodicamente
- Use apenas as permissões mínimas necessárias