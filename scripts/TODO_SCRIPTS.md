# TODO Scripts - Portal KNN

**Projeto:** KNN Portal Journey Club Backend - Scripts
**Data:** Janeiro 2025
**Status:** Análise e Limpeza em Andamento
**Última Atualização:** Janeiro 2025

---

## 📊 Status Geral dos Scripts

**🔄 ANÁLISE EM ANDAMENTO** - Pasta scripts/ contém 35+ arquivos organizados em 6 categorias. Necessária análise para identificar scripts obsoletos, duplicados ou desnecessários.

---

## 📁 Estrutura Atual dos Scripts

### ✅ Bem Organizados

#### 🐛 debug/ - Scripts de Debug (Recém Organizados)

- **cache/** - Scripts de teste de cache
- **firestore/** - Scripts de teste do Firestore
- **logos/** - Scripts de teste de logos
- **partners/** - Scripts de teste de parceiros
- **tenant/** - Scripts de teste de tenant

#### 🚀 development/ - Scripts de Desenvolvimento

- `analyze_partners_images.py` - Análise de imagens de parceiros
- `create_test_entities.py` - Criação de entidades de teste
- `generate_test_data.py` - Geração de dados de teste
- `seed_dev.py` - Seed para ambiente de desenvolvimento

#### 🧪 testing/ - Scripts de Teste Automatizado

- `README.md` - Documentação dos testes
- `report_generator.py` - Gerador de relatórios
- `requirements.txt` - Dependências dos testes
- `run_all_tests.py` - Executor de todos os testes
- `start_backend.py` - Inicializador do backend para testes
- `test_audience_implementation.py` - Testes de audiência
- `test_config.py` - Configurações de teste
- `test_runner.py` - Executor de testes
- `test_suite.py` - Suite de testes

#### 🔄 migration/ - Scripts de Migração

- `migrate_audience_field.py` - Migração de campo de audiência
- `migrate_favorites_to_separated_collections.py` - Migração de favoritos
- `remove_active_field.py` - Remoção de campo ativo
- `update_courses_structure.py` - Atualização de estrutura de cursos

### ⚠️ Necessitam Análise

#### 🔧 maintenance/ - Scripts de Manutenção (15 arquivos)

**Status:** 🔍 **ANÁLISE NECESSÁRIA** - Muitos scripts, possível duplicação

- `archive_old_reports.py` - Arquivamento de relatórios antigos
- `check_courses.py` - Verificação de cursos
- `check_partners.py` - Verificação de parceiros
- `cleanup_expired_codes.py` - Limpeza de códigos expirados
- `courses_operations.py` - Operações de cursos
- `debug_courses.py` - Debug de cursos ⚠️ (Possível duplicação com debug/)
- `find_correct_bucket.py` - Localização de bucket correto
- `setup_cleanup_scheduler.py` - Configuração de limpeza agendada
- `split_firestore_export.py` - Divisão de export do Firestore
- `standardize_student_structure.py` - Padronização de estrutura de estudantes
- `sync_users_collection.py` - Sincronização de coleção de usuários
- `test_firebase_connection.py` - Teste de conexão Firebase ⚠️ (Possível duplicação)
- `validate_artifacts.py` - Validação de artefatos
- `verify_auth_sync.py` - Verificação de sincronização de auth
- `verify_employees_upload.py` - Verificação de upload de funcionários
- `verify_users_collection.py` - Verificação de coleção de usuários

#### 📄 docs/ - Documentação

- `relatorio_importacao_firestore_20250905_163043.md` - Relatório específico ⚠️ (Possível arquivo temporário)

#### 📚 examples/ - Exemplos

- `multi_database_example.py` - Exemplo de multi-banco

#### 📁 Raiz da pasta scripts/

- `populate_courses.py` - População de cursos ⚠️ (Verificar se deve estar em development/)
- `run_server.py` - Executor do servidor ⚠️ (Verificar se deve estar em development/)

---

## 🎯 Tarefas de Análise e Limpeza

### 🔄 EM ANDAMENTO

#### [SCRIPTS_001] Análise de Scripts de Manutenção

- **Status:** 🔄 **EM ANDAMENTO**
- **Prioridade:** Alta
- **Duração Estimada:** 1 dia

**Checklist:**

- [ ] **Identificar duplicações:**
  - [ ] Comparar `debug_courses.py` com scripts em `debug/`
  - [ ] Verificar `test_firebase_connection.py` vs scripts de teste
  - [ ] Analisar sobreposição entre scripts de verificação

- [ ] **Categorizar por funcionalidade:**
  - [ ] Scripts de verificação/validação
  - [ ] Scripts de limpeza/manutenção
  - [ ] Scripts de sincronização
  - [ ] Scripts de debug/teste

- [ ] **Avaliar necessidade:**
  - [ ] Identificar scripts não utilizados
  - [ ] Verificar scripts com funcionalidade obsoleta
  - [ ] Documentar propósito de cada script

### 📋 PENDENTE

#### [SCRIPTS_002] Reorganização de Arquivos da Raiz

- **Status:** 📋 **PENDENTE**
- **Prioridade:** Média
- **Duração Estimada:** 30 minutos

**Checklist:**

- [ ] **Mover arquivos para categorias apropriadas:**
  - [ ] `populate_courses.py` → `development/` ou `maintenance/`
  - [ ] `run_server.py` → `development/` ou `testing/`

#### [SCRIPTS_003] Limpeza de Arquivos Temporários

- **Status:** 📋 **PENDENTE**
- **Prioridade:** Baixa
- **Duração Estimada:** 15 minutos

**Checklist:**

- [ ] **Remover arquivos temporários:**
  - [ ] Avaliar `docs/relatorio_importacao_firestore_20250905_163043.md`
  - [ ] Verificar se é arquivo histórico ou temporário
  - [ ] Mover para local apropriado ou remover

#### [SCRIPTS_004] Consolidação de Funcionalidades

- **Status:** 📋 **PENDENTE**
- **Prioridade:** Baixa
- **Duração Estimada:** 2-3 horas

**Checklist:**

- [ ] **Unificar scripts similares:**
  - [ ] Consolidar scripts de verificação de usuários
  - [ ] Unificar scripts de verificação de cursos
  - [ ] Criar utilitários centralizados

#### [SCRIPTS_005] Documentação e Padronização

- **Status:** 📋 **PENDENTE**
- **Prioridade:** Média
- **Duração Estimada:** 1 dia

**Checklist:**

- [ ] **Criar documentação:**
  - [ ] README para cada categoria
  - [ ] Documentar propósito de cada script
  - [ ] Exemplos de uso para scripts principais

- [ ] **Padronizar estrutura:**
  - [ ] Implementar logging consistente
  - [ ] Padronizar argumentos de linha de comando
  - [ ] Adicionar docstrings e type hints

---

## ✅ Limpeza Realizada

### Arquivos Removidos

1. **Relatório temporário removido:**
   - ❌ `docs/relatorio_importacao_firestore_20250905_163043.md` - Arquivo temporário específico de data removido
   - ❌ `docs/` - Pasta vazia removida

2. **Arquivos reorganizados:**
   - 📁 `populate_courses.py` → `development/populate_courses.py`
   - 📁 `run_server.py` → `development/run_server.py`

### Scripts Mantidos (Análise Concluída)

1. **maintenance/debug_courses.py** - ✅ **MANTIDO**
   - Funcionalidade específica para debug de cursos no Firestore
   - Não duplica funcionalidade dos scripts em debug/
   - Script útil para manutenção

2. **maintenance/test_firebase_connection.py** - ✅ **MANTIDO**
   - Script específico para testar conexão Firebase antes de uploads
   - Funcionalidade diferente dos testes automatizados
   - Útil para diagnóstico de problemas de conexão

---

## 🚨 Scripts Identificados para Possível Remoção

### ✅ Limpeza Concluída

1. **Arquivos Temporários:** ✅ **REMOVIDOS**
   - ~~`docs/relatorio_importacao_firestore_20250905_163043.md`~~ - Removido
   - ~~Pasta `docs/` vazia~~ - Removida

2. **Reorganização:** ✅ **CONCLUÍDA**
   - ~~`populate_courses.py`~~ - Movido para `development/`
   - ~~`run_server.py`~~ - Movido para `development/`

### ⚠️ Análise Concluída - Scripts Mantidos

1. **Scripts Analisados e Mantidos:**
   - `maintenance/debug_courses.py` - Funcionalidade única mantida
   - `maintenance/test_firebase_connection.py` - Funcionalidade específica mantida

### ✅ Scripts Essenciais (Manter)

1. **Categoria testing/:** Todos os scripts (sistema de testes automatizados)
2. **Categoria development/:** Todos os scripts (desenvolvimento ativo)
3. **Categoria migration/:** Todos os scripts (histórico de migrações)
4. **Categoria debug/:** Todos os scripts (recém organizados)

---

## 📊 Métricas Finais

- **Total de arquivos analisados:** 35+ scripts
- **Arquivos removidos:** 1 (relatório temporário)
- **Pastas removidas:** 1 (docs/ vazia)
- **Arquivos reorganizados:** 2 (movidos para development/)
- **Scripts analisados e mantidos:** 2 (funcionalidades únicas confirmadas)
- **Categorias organizadas:** 6 (debug, development, testing, migration, maintenance, examples)
- **Status final:** ✅ **LIMPEZA CONCLUÍDA**

## 🎯 Resultados da Limpeza

### ✅ Objetivos Alcançados

1. **Estrutura limpa:** Raiz da pasta scripts/ organizada
2. **Arquivos temporários removidos:** Relatórios específicos de data eliminados
3. **Reorganização concluída:** Scripts movidos para categorias apropriadas
4. **Análise de duplicações:** Scripts analisados e funcionalidades únicas confirmadas
5. **Documentação atualizada:** TODO_SCRIPTS.md reflete estado atual

### 📁 Estrutura Final Organizada

```text
scripts/
├── README.md
├── TODO_SCRIPTS.md ✨ (novo)
├── debug/
│   ├── cache/
│   ├── firestore/
│   ├── logos/
│   ├── partners/
│   └── tenant/
├── development/
│   ├── analyze_partners_images.py
│   ├── create_test_entities.py
│   ├── generate_test_data.py
│   ├── populate_courses.py ✨ (movido)
│   ├── run_server.py ✨ (movido)
│   └── seed_dev.py
├── examples/
│   └── multi_database_example.py
├── maintenance/
│   ├── [15 scripts de manutenção] ✅ (analisados e mantidos)
├── migration/
│   ├── [4 scripts de migração]
└── testing/
    ├── [9 arquivos de teste automatizado]
```

---

> **Última Atualização:** Janeiro 2025
> **Responsável:** Equipe Backend
> **Status:** ✅ **LIMPEZA CONCLUÍDA**
> **Próxima ação:** Manutenção contínua conforme necessário
