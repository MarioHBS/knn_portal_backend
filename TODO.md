# TODO - Portal de Benefícios KNN

## ✅ Concluído

### Reorganização de Scripts (Janeiro 2025)

- [x] Análise completa da pasta `scripts/` e subpastas
- [x] Identificação e remoção de scripts obsoletos
- [x] Reorganização por categoria (development, maintenance, migration, testing)
- [x] Limpeza da pasta `scripts/temp/`
- [x] Atualização da documentação (READMEs)

#### Scripts Reorganizados

**Movidos para `development/`:**

- `analyze_and_organize_images.py` - Análise e organização de imagens
- `analyze_partners_images.py` - Análise específica de imagens de parceiros
- `create_test_entities.py` - Criação de entidades de teste

**Movidos para `maintenance/`:**

- `verify_auth_sync.py` - Verificação de sincronização de autenticação
- `verify_users_collection.py` - Verificação da coleção de usuários
- `verify_employees_upload.py` - Verificação de upload de funcionários
- `sync_users_collection.py` - Sincronização da coleção de usuários

**Scripts Removidos (obsoletos):**

- Scripts de debug pontuais já executados
- Scripts de conversão de dados já aplicados
- Scripts de export/import específicos concluídos
- Scripts de limpeza e upload pontuais finalizados

## 🔄 Em Andamento

*Nenhuma tarefa em andamento no momento*

## 📋 Pendente

### Melhorias de Código

- [ ] Implementar validação com Ruff em todos os arquivos Python
- [ ] Adicionar docstrings nos scripts reorganizados
- [ ] Revisar e padronizar tratamento de erros

### Documentação

- [ ] Criar guias de uso para scripts de maintenance
- [ ] Documentar processo de criação de entidades de teste
- [ ] Atualizar documentação da API

### Testes

- [ ] Implementar testes unitários para scripts críticos
- [ ] Validar funcionamento dos scripts reorganizados
- [ ] Criar suite de testes automatizados

### Infraestrutura

- [ ] Configurar CI/CD para validação automática
- [ ] Implementar logs estruturados nos scripts
- [ ] Configurar monitoramento de execução

## 🚫 Bloqueado

*Nenhuma tarefa bloqueada no momento*

## 📝 Notas

- Scripts temporários devem usar prefixo `temp_` e ser colocados em `scripts/temp/`
- Todos os scripts devem seguir as convenções do projeto (Ruff, docstrings)
- Operações em massa requerem confirmação explícita do usuário
- Credenciais devem ser mantidas na pasta `/credentials/` e ignoradas pelo Git

## 🎯 Próximas Prioridades

1. Implementar validação com Ruff nos scripts reorganizados
2. Adicionar testes unitários para scripts críticos
3. Documentar processo de uso dos scripts de maintenance
4. Configurar CI/CD para validação automática

---
*Última atualização: Setembro 2025*
