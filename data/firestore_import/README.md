# Firestore Import - Documentação e Scripts

Esta pasta contém todos os arquivos relacionados à configuração, importação e gerenciamento de dados do Firebase/Firestore.

## 📁 Estrutura de Arquivos

### 📋 Documentação

- `README.md` - Este arquivo de documentação
- `COMO_CONFIGURAR_CREDENCIAIS.md` - Guia para configurar credenciais do Firebase
- `COMO_OBTER_CHAVE_KNN_BENEFITS.md` - Instruções para obter chaves do projeto knn-benefits
- `RELATORIO_IMPORTACAO.md` - Relatório detalhado das importações realizadas
- `FIRESTORE_DATA_IMPORT_GUIDE.md` - Guia completo de importação de dados
- `FIREBASE_SETUP.md` - Configuração inicial do Firebase

### 🔧 Scripts de Importação

- `import_to_firestore.py` - Script principal de importação (com suporte a emulador)
- `import_with_service_account.py` - Importação usando chaves de conta de serviço
- `list_firestore_databases.py` - Lista bancos de dados disponíveis

### 👤 Scripts de Usuários Admin

- `setup_admin_user.py` - Configuração de usuário admin para projeto default
- `create_admin_user_knn_benefits.py` - Criação de usuário admin para knn-benefits

### 🧪 Scripts de Teste

- `test_default_database.py` - Testa conexão com banco default
- `test_knn_benefits_database.py` - Testa conexão com banco knn-benefits
- `test_api_comprehensive.py` - Testes abrangentes da API
- `test_api_endpoints.py` - Testes específicos de endpoints

### 📊 Dados

- `firestore_data_default.json` - Dados formatados para importação (banco default)
- `firestore_data_production.json` - Dados formatados para importação (banco produção)
- `firestore_export_default.json` - Dados no formato de exportação do Firestore (default)
- `firestore_export_production.json` - Dados no formato de exportação do Firestore (produção)

### 🔐 Credenciais (não versionadas)

- `default-service-account-key.json` - Chave para projeto default (gitignore)
- `knn-benefits-service-account-key.json` - Chave para projeto knn-benefits (gitignore)

## 🚀 Como Usar

1. **Configurar Credenciais**: Siga o guia em `COMO_CONFIGURAR_CREDENCIAIS.md`
2. **Importar Dados**: Execute `python import_with_service_account.py`
3. **Testar Conexão**: Execute os scripts de teste conforme necessário
4. **Criar Usuários Admin**: Use os scripts de setup de usuário admin

## ⚠️ Segurança

- Arquivos `*service-account-key.json` estão no `.gitignore`
- Nunca commite credenciais no repositório
- Use variáveis de ambiente em produção

## 📝 Notas

- Todos os scripts suportam múltiplos projetos Firebase
- Dados são organizados por ambiente (default/production)
- Scripts de teste geram relatórios automaticamente
