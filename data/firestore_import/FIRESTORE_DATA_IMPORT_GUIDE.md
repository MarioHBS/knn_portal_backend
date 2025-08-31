# Guia de Importação de Dados para Firestore

## Resumo

Este guia explica como importar os dados de alunos e funcionários para os dois bancos de dados Firestore:
- **default** (knn-portal-dev) - Para testes
- **production** (knn-benefits) - Para produção

## Dados Processados

✅ **74 alunos** transformados e preparados
✅ **12 funcionários** transformados e preparados
✅ Dados formatados para ambos os bancos
✅ Scripts de importação gerados

## Arquivos Gerados

Todos os arquivos estão localizados em: `data/firestore_import/`

### Arquivos de Dados
- `firestore_data_default.json` - Dados para o banco de testes
- `firestore_data_production.json` - Dados para o banco de produção
- `firestore_export_default.json` - Formato de exportação para testes
- `firestore_export_production.json` - Formato de exportação para produção

### Scripts e Relatórios
- `import_to_firestore.py` - Script automatizado de importação
- `migration_report.json` - Relatório detalhado da preparação

## Estrutura dos Dados Transformados

### Coleção `students`
```json
{
  "tenant_id": "knn-dev-tenant",
  "cpf_hash": "hash_seguro_do_cpf",
  "nome_aluno": "Nome do Aluno",
  "curso": "SEEDS 4",
  "ocupacao_aluno": "Profissão",
  "email_aluno": "email@exemplo.com",
  "celular_aluno": "98999999999",
  "cep_aluno": "65000-000",
  "bairro": "Nome do Bairro",
  "complemento_aluno": "Complemento",
  "nome_responsavel": "Nome do Responsável",
  "email_responsavel": "responsavel@exemplo.com",
  "active_until": "2026-08-28",
  "created_at": "2025-08-28T17:35:56.008419",
  "updated_at": "2025-08-28T17:35:56.008419"
}
```

### Coleção `employees`
```json
{
  "tenant_id": "knn-dev-tenant",
  "cpf_hash": "hash_seguro_do_cpf",
  "nome_funcionario": "Nome do Funcionário",
  "cargo": "PROFESSOR",
  "email_funcionario": "funcionario@exemplo.com",
  "telefone_funcionario": "98999999999",
  "cep_funcionario": "65000-000",
  "active": true,
  "created_at": "2025-08-28T17:35:56.008419",
  "updated_at": "2025-08-28T17:35:56.008419"
}
```

## Métodos de Importação

### Método 1: Script Automatizado (Recomendado)

#### Pré-requisitos
1. Configure as credenciais do Firebase para ambos os projetos
2. Instale o Firebase Admin SDK (já instalado no projeto)

#### Configuração de Credenciais

**Opção A: Credenciais Padrão do Google Cloud**
```bash
# Instalar Google Cloud CLI
# Fazer login
gcloud auth application-default login

# Definir projeto padrão
gcloud config set project knn-portal-dev
```

**Opção B: Arquivo de Credenciais de Serviço**
1. No Console do Firebase, vá para "Configurações do Projeto"
2. Aba "Contas de Serviço"
3. Clique em "Gerar nova chave privada"
4. Salve o arquivo JSON em local seguro
5. Configure a variável de ambiente:
```bash
$env:GOOGLE_APPLICATION_CREDENTIALS="caminho/para/credenciais.json"
```

#### Executar Importação
```bash
# Navegar para o diretório do projeto
cd P:\ProjectsWEB\PRODUCAO\knn_portal_backend

# Executar script de importação
python data/firestore_import/import_to_firestore.py
```

### Método 2: Importação Manual via Console Firebase

#### Para o Banco de Testes (default)
1. Acesse o [Console do Firebase](https://console.firebase.google.com/)
2. Selecione o projeto `knn-portal-dev`
3. Vá para "Firestore Database"
4. Clique em "Importar"
5. Selecione o arquivo `firestore_export_default.json`
6. Confirme a importação

#### Para o Banco de Produção
1. Acesse o [Console do Firebase](https://console.firebase.google.com/)
2. Selecione o projeto `knn-benefits`
3. Vá para "Firestore Database"
4. Clique em "Importar"
5. Selecione o arquivo `firestore_export_production.json`
6. Confirme a importação

### Método 3: Importação via Firebase CLI

#### Instalar Firebase CLI
```bash
npm install -g firebase-tools
```

#### Fazer Login
```bash
firebase login
```

#### Importar para Banco de Testes
```bash
firebase firestore:import data/firestore_import/firestore_export_default.json --project knn-portal-dev
```

#### Importar para Banco de Produção
```bash
firebase firestore:import data/firestore_import/firestore_export_production.json --project knn-benefits
```

## Validação da Importação

### Verificar via Console Firebase
1. Acesse o Console do Firebase
2. Vá para "Firestore Database"
3. Verifique as coleções:
   - `students` deve ter 74 documentos
   - `employees` deve ter 12 documentos

### Verificar via Script Python
```python
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar Firebase
app = firebase_admin.initialize_app(options={"projectId": "knn-portal-dev"})
db = firestore.client()

# Contar documentos
students_count = len(list(db.collection('students').limit(100).stream()))
employees_count = len(list(db.collection('employees').limit(100).stream()))

print(f"Estudantes: {students_count}")
print(f"Funcionários: {employees_count}")
```

## Estrutura Multi-Tenant

Todos os dados incluem o campo `tenant_id: "knn-dev-tenant"` para suporte multi-tenant. Isso permite:
- Isolamento de dados por cliente
- Consultas filtradas por tenant
- Escalabilidade para múltiplos clientes

## Segurança dos Dados

### Hashing de CPF
- CPFs são convertidos em hashes SHA-256
- Não é possível recuperar o CPF original
- Mantém a capacidade de busca e comparação

### Dados Fictícios
- CPFs gerados são fictícios baseados no ID do registro
- Estrutura: `000XXXXXXXX` para alunos, `111XXXXXXXX` para funcionários

## Troubleshooting

### Erro: "Permission denied"
- Verifique se as credenciais estão configuradas corretamente
- Confirme se o usuário tem permissões no projeto Firebase
- Verifique as regras de segurança do Firestore

### Erro: "Project not found"
- Confirme se os IDs dos projetos estão corretos:
  - `knn-portal-dev` para testes
  - `knn-benefits` para produção
- Verifique se você tem acesso aos projetos

### Erro: "Quota exceeded"
- O Firestore tem limites de operações por segundo
- O script usa batches de 500 documentos para otimizar
- Se necessário, adicione delays entre batches

### Dados não aparecem
- Verifique se a importação foi concluída sem erros
- Confirme se está visualizando o projeto correto
- Verifique as regras de segurança do Firestore

## Próximos Passos

1. **Configurar Regras de Segurança**
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /students/{document} {
         allow read, write: if request.auth != null &&
           resource.data.tenant_id == "knn-dev-tenant";
       }
       match /employees/{document} {
         allow read, write: if request.auth != null &&
           resource.data.tenant_id == "knn-dev-tenant";
       }
     }
   }
   ```

2. **Configurar Índices**
   - Criar índices compostos para consultas por `tenant_id`
   - Otimizar consultas frequentes

3. **Backup e Monitoramento**
   - Configurar backups automáticos
   - Implementar monitoramento de uso
   - Configurar alertas de quota

4. **Testes**
   - Testar operações CRUD via API
   - Validar filtros por tenant
   - Verificar performance das consultas

## Contatos e Suporte

- **Documentação Firebase**: https://firebase.google.com/docs/firestore
- **Console Firebase**: https://console.firebase.google.com/
- **Status Firebase**: https://status.firebase.google.com/

---

**Data de Criação**: 28 de Agosto de 2025
**Última Atualização**: 28 de Agosto de 2025
**Versão**: 1.0
