# Como Configurar Credenciais do Firebase

## Problema Atual

O script de importação está falhando porque não consegue encontrar as credenciais do Firebase. Você precisa configurar a autenticação para acessar o Firestore.

## Soluções Disponíveis

### Opção 1: Chave de Conta de Serviço (Recomendado)

#### Passo 1: Obter a Chave de Conta de Serviço

1. **Acesse o Firebase Console:**
   - Vá para [Firebase Console](https://console.firebase.google.com/)
   - Selecione o projeto `knn-benefits`

2. **Navegue para Configurações:**
   - Clique no ícone de engrenagem (⚙️) no menu lateral
   - Selecione "Configurações do projeto"

3. **Vá para a aba "Contas de serviço":**
   - Clique na aba "Contas de serviço"
   - Role para baixo até "SDK Admin do Firebase"

4. **Gere uma nova chave:**
   - Clique em "Gerar nova chave privada"
   - Confirme clicando em "Gerar chave"
   - Um arquivo JSON será baixado automaticamente

#### Passo 2: Configurar a Chave

1. **Renomeie o arquivo:**
   - Renomeie o arquivo baixado para `service-account-key.json`

2. **Mova para o diretório correto:**
   - Coloque o arquivo na pasta: `data/firestore_import/`
   - Caminho completo: `p:\ProjectsWEB\PRODUCAO\knn_portal_backend\data\firestore_import\service-account-key.json`

3. **Execute o script:**
   ```powershell
   python import_with_service_account.py
   ```

### Opção 2: Variável de Ambiente

Se você já tem o arquivo de chave, pode configurar uma variável de ambiente:

```powershell
# No PowerShell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\caminho\para\sua\chave.json"
```

Ou adicione no arquivo `.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=C:\caminho\para\sua\chave.json
```

### Opção 3: Google Cloud CLI (Alternativa)

Se você tem acesso ao projeto no Google Cloud:

1. **Instale o Google Cloud CLI** (se não tiver):
   - Baixe de: https://cloud.google.com/sdk/docs/install

2. **Faça login:**
   ```powershell
   gcloud auth login
   gcloud config set project knn-benefits
   gcloud auth application-default login
   ```

## Verificação

Para verificar se as credenciais estão funcionando:

```powershell
# Teste a conexão
python -c "from google.cloud import firestore; db = firestore.Client(); print('✅ Conexão bem-sucedida!')"
```

## Estrutura de Arquivos Esperada

```
data/firestore_import/
├── service-account-key.json          # ← Sua chave aqui
├── import_with_service_account.py
├── firestore_data_default.json
├── firestore_data_production.json
└── COMO_CONFIGURAR_CREDENCIAIS.md
```

## Troubleshooting

### Erro: "Your default credentials were not found"
- **Causa:** Nenhuma credencial configurada
- **Solução:** Siga a Opção 1 acima

### Erro: "Permission denied"
- **Causa:** A conta de serviço não tem permissões suficientes
- **Solução:** No Firebase Console, vá para "Usuários e permissões" e garanta que a conta de serviço tem papel de "Editor" ou "Proprietário"
- **Para o projeto knn-benefits**: Consulte o guia específico [COMO_OBTER_CHAVE_KNN_BENEFITS.md](./COMO_OBTER_CHAVE_KNN_BENEFITS.md)

### Erro: "Project not found"
- **Causa:** ID do projeto incorreto
- **Solução:** Verifique se o projeto `knn-benefits` existe e você tem acesso

## Próximos Passos

1. ✅ Obter chave de conta de serviço
2. ✅ Colocar arquivo na pasta correta
3. ✅ Executar `python import_with_service_account.py`
4. ✅ Verificar se os dados foram importados no Firebase Console

## Segurança

⚠️ **IMPORTANTE:**
- Nunca commite o arquivo `service-account-key.json` no Git
- O arquivo já está no `.gitignore`
- Mantenha a chave segura e não compartilhe

---

**Precisa de ajuda?** Verifique se:
1. Você tem acesso ao projeto Firebase `knn-benefits`
2. O arquivo de chave está no local correto
3. O arquivo não está corrompido (deve ser um JSON válido)
