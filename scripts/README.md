# Scripts do Portal de Benefícios KNN

Este diretório contém scripts organizados por categoria para facilitar a manutenção e desenvolvimento do projeto.

## Estrutura de Pastas

### 📁 development/
Scripts para desenvolvimento e preparação de dados:
- `generate_test_data.py` - Gera dados simulados para testes locais
- `prepare_firestore_data.py` - Prepara dados para formato Firestore
- `seed_dev.py` - Popula dados de desenvolvimento/QA
- `analyze_and_organize_images.py` - Análise e organização de imagens de parceiros
- `analyze_partners_images.py` - Análise específica de imagens de parceiros
- `create_test_entities.py` - Criação de entidades de teste (Aluno, Funcionário, Parceiro)

### 📁 maintenance/
Scripts para manutenção e verificação do sistema:
- `check_courses.py` - Verifica presença de cursos no Firestore
- `debug_courses.py` - Lista cursos para depuração
- `validate_artifacts.py` - Valida artefatos gerados do projeto
- `courses_operations.py` - **Script consolidado** para operações de cursos (check, debug, populate)
- `verify_auth_sync.py` - Verificação de sincronização entre Firestore e Firebase Auth
- `verify_users_collection.py` - Verificação da integridade da coleção de usuários
- `verify_employees_upload.py` - Verificação de upload de funcionários
- `sync_users_collection.py` - Sincronização da coleção de usuários com Firebase Auth

### 📁 migration/
Scripts de migração de dados e estruturas:
- `migrate_audience_field.py` - Migra campo target_profile para audience
- `migrate_data_to_firestore.py` - Migra dados de JSON para Firestore
- `remove_active_field.py` - Remove campo 'active' dos cursos
- `update_courses_structure.py` - Atualiza estrutura dos cursos

### 📁 testing/
Scripts para testes e validação:
- `test_audience_implementation.py` - Testa validação do modelo audience
- `test_endpoints.py` - Testa endpoints do Portal de Benefícios
- `test_suite.py` - **Suite consolidada** de testes (audience, endpoints, filtragem)

### 📁 temp/
Scripts temporários (não versionados):
- **Pasta limpa e reorganizada** - Scripts obsoletos foram removidos
- Scripts úteis foram movidos para pastas apropriadas (development, maintenance)
- Contém apenas README.md para orientação de uso
- Arquivos com prefixo `temp_` são automaticamente ignorados pelo Git

## Scripts na Raiz

### Scripts Principais
- `populate_courses.py` - Popula base de dados com cursos disponíveis
- `run_server.py` - Inicia servidor FastAPI para testes locais

## Convenções

- Scripts temporários devem ser colocados na pasta `temp/` ou usar prefixo `temp_`
- Scripts de migração são executados uma única vez e mantidos para histórico
- Scripts de desenvolvimento são reutilizáveis para setup de ambiente
- Scripts de manutenção são para verificações periódicas
- Scripts de teste validam funcionalidades específicas

## Uso

Todos os scripts devem ser executados a partir da raiz do projeto:

```bash
# Exemplo: executar script de desenvolvimento
python scripts/development/seed_dev.py

# Exemplo: executar script de manutenção
python scripts/maintenance/check_courses.py

# Scripts consolidados com múltiplas operações:
python scripts/maintenance/courses_operations.py check
python scripts/maintenance/courses_operations.py debug
python scripts/maintenance/courses_operations.py populate

python scripts/testing/test_suite.py
python scripts/testing/test_suite.py http://localhost:8080
```

## Gitignore

A pasta `temp/` e arquivos com padrões `temp_*.py` e `*_temp.py` são automaticamente ignorados pelo Git conforme configurado no `.gitignore`.