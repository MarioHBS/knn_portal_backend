# Scripts do Portal de Benefícios KNN

Este diretório contém scripts auxiliares (nunca código de produção — isso vive
em `src/`), organizados em 6 categorias fixas. Todos os scripts devem ser
executados a partir da raiz do backend
(`knn_portal_journey_club_backend/`).

> Reescrito em 2026-09-18 (stage `limpeza-dados-infra`) a partir do disco real
> — a versão anterior deste arquivo citava pastas/arquivos que já não
> existiam (`temp/` como categoria, `check_courses.py`,
> `verify_auth_sync.py`, `test_endpoints.py`) e nunca mencionava `debug/` nem
> `examples/`.

## Critério de cada categoria

| Categoria | Critério |
| --- | --- |
| `debug/` | Diagnóstico/inspeção — só lê dados, não altera nada. Ferramentas reutilizáveis para investigar um problema (estrutura de uma coleção, conectividade, mismatch de tenant), não script de uma investigação específica já resolvida. |
| `development/` | Setup de ambiente de desenvolvimento/QA — gera dados de teste, popula coleções, gera docs/tokens locais. |
| `testing/` | Testes automatizados ou semi-automatizados dos endpoints da API (fora da suíte `pytest` em `tests/`). `testing/e2e/` guarda o fluxo completo de autenticação + jornada ponta a ponta por perfil. |
| `migration/` | Scripts de correção/migração de dados **já executados** — mantidos como registro histórico, não para reexecução rotineira. |
| `maintenance/` | Operações reutilizáveis de manutenção/administração — podem ser executadas de novo quando necessário (seed, sync, cleanup, validação). |
| `examples/` | Exemplos autocontidos e simplificados de uso da API — propositalmente mais simples que a suíte de `testing/`, para servir de referência rápida. |

Não existe mais `scripts/temp/`: era 100% gitignorada/sem histórico, tinha
crescido para 105+ arquivos e sido tratada por engano como "descartável em
bloco" — a revisão desta stage (2026-09-18) confirmou que a maioria era
investigação pontual de bugs já resolvidos, mas ~29 scripts eram ferramentas
reais e foram migrados para as categorias abaixo antes de a pasta ser
removida. Não recriar essa pasta; um script realmente temporário deve ter o
prefixo `temp_` e viver dentro da categoria a que já pertence (será
descartado quando a investigação terminar).

## `debug/`

Inspeção/diagnóstico, sem efeitos colaterais:

- `check_firestore_databases.py` — em qual banco Firestore nomeado (ver
  `FIRESTORE_DATABASES_LIST` em `config.py`) um dado está.
- `check_tenant.py` — tenant_id de um documento específico.
- `debug_firestore_client.py` / `debug_firestore_query.py` /
  `debug_firestore_simple.py` / `debug_firestore_structure.py` — depuração de
  conectividade/consulta/estrutura do Firestore em diferentes ângulos.
- `debug_benefit_structure.py` — estrutura de documentos de benefícios.
- `investigate_firestore_structure.py` — estrutura geral de um documento.
- `temp_inspect_courses_structure.py` — compara estrutura real de `courses`
  com `COURSES_MAP` do código.
- `test_database_connection.py` / `test_firestore_direct.py` /
  `test_postgres_connection.py` — smoke test de conectividade (apesar do
  prefixo `test_`, não são testes pytest).
- `get_benefits_collection.py`, `get_courses_collection.py`,
  `get_employees_collection.py`, `get_metadata_collection.py`,
  `get_partners_collection.py`, `get_students_collection.py` — dump/inspeção
  de cada coleção do Firestore (uma por tipo de entidade).
- `cache/debug_fresh_data.py` — limpa cache local e verifica dados atuais.
- `firestore/debug_firestore_raw.py` — script consolidado de debug de
  Firestore (conectividade + listagem + acesso raw).
- `partners/debug_partners_comprehensive.py` — script consolidado de debug
  de parceiros (estrutura + query + acesso raw + simulação de endpoint).
- `tenant/debug_tenant_mismatch.py` — compara tenant_id do JWT com o do
  Firestore.

## `development/`

- `analyze_partners_images.py` — analisa estrutura de imagens dos parceiros.
- `create_test_entities.py` — cria Aluno/Funcionário/Parceiro de teste no
  Firebase.
- `generate_openapi_docs.py` — gera a documentação OpenAPI (fonte do
  `openapi.yaml` na raiz do backend).
- `generate_test_data.py` — simula dados para testes locais.
- `generate_test_token.py` — gera JWT de teste com o tenant correto.
- `populate_courses.py` — popula a base com os cursos disponíveis.
- `seed_dev.py` — gera dataset completo de dev/QA (5 alunos, 3 parceiros, 4
  promoções).

## `testing/`

- `test_config.py`, `test_runner.py`, `report_generator.py`,
  `start_backend.py`, `run_all_tests.py` — infraestrutura da suíte
  (configuração centralizada, executor, relatórios, gerenciamento do
  backend local).
- `setup_auth_test_env.py`, `quick_auth_test.py` — setup/smoke test rápido
  de autenticação.
- `debug_partner_benefits_search.py`, `fix_partner_benefits_structure.py` —
  depuração/correção pontual ainda em uso da busca de benefícios por
  parceiro.
- `test_audience_implementation.py`, `test_benefits_comparison.py`,
  `test_benefits_direct_access.py`, `test_endpoint_direct.py`,
  `test_partner_benefits_direct.py`, `test_student_partner_details.py`,
  `test_suite.py`, `verify_partner_entity_mapping.py` — testes de endpoints
  específicos.
- `requirements.txt` — dependências desta suíte (`requests`, `aiohttp` etc.,
  separadas do `requirements.txt` principal do backend).
- `e2e/` — ex-`scripts/complete_flow/` (absorvido nesta stage 2026-09-18):
  suíte completa de autenticação (Firebase → JWT → endpoint autenticado) e
  jornada ponta a ponta por perfil (`admin_auth_test.py`,
  `employee_auth_test.py`, `partner_auth_test.py`, `student_auth_test.py`,
  seus atalhos `quick_*_test.py`, `base_auth_test.py` com a lógica comum,
  `complete_auth_flow_test.py`, `auth_test_runner.py`, `generate_token.py`).
  Ver `e2e/README.md` para o histórico da investigação que deu origem a
  este fluxo.

**Nota conhecida:** `base_auth_test.py`, `quick_admin_test.py` e
`quick_student_test.py` também existem em `scripts/examples/`, com conteúdo
parcialmente sobreposto (diff confirmado 2026-09-18): `examples/` guarda
versões deliberadamente mais simples e autocontidas (import via
`sys.path` relativo ao próprio diretório), enquanto `testing/e2e/` guarda as
versões completas usadas pela suíte de regressão. Mantidos separados de
propósito — unificar exigiria mudar o mecanismo de import de `examples/`,
fora do escopo desta stage (organização de arquivos, não redesenho de
código).

## `migration/`

Scripts de correção/migração já executados, mantidos como registro
histórico (não reexecutar sem revisar o estado atual dos dados primeiro):

- `add_fields_to_courses.py`, `update_courses_structure.py`,
  `remove_active_field.py`, `migrate_audience_field.py`,
  `migrate_favorites_to_separated_collections.py` — migrações estruturais
  de `courses`/campos de modelo já aplicadas.
- `create_firestore_index.py` — criação do índice composto
  `partners(tenant_id, active, trade_name)`.
- `fix_benefits_tenant_id.py`, `fix_document_tenant.py`,
  `fix_partner_document.py`, `fix_partners_active.py`,
  `fix_partners_active_field.py`, `fix_partners_tenant.py`,
  `fix_student_name.py`, `revert_benefits_tenant_id.py`,
  `temp_clean_courses_fields.py` — correções pontuais de dados já aplicadas
  (tenant_id, campo `active`, nome de estudante, limpeza de campos extras em
  `courses`).
- `get_logos_urls.py` / `update_partners_logos.py` — par de scripts do
  backfill de URLs de logos no Storage (já executado).

## `maintenance/`

Operações reutilizáveis — podem ser executadas de novo quando necessário:

- `add_admin_user.py` — cria usuário admin.
- `archive_old_reports.py` — arquiva relatórios antigos.
- `check_partners_json.py` — confere contagem de parceiros/funcionários num
  export JSON (`data/firestore_export/firestore_employees_partners.json`).
- `cleanup_expired_codes.py` — limpa códigos de validação expirados.
- `copy_student_document.py` — copia um documento de aluno entre
  tenants/ambientes.
- `courses_operations.py` — **script consolidado** de operações de cursos
  (`check`/`debug`/`populate` via argumento de linha de comando).
- `fix_benefits_tenant.py` — define/atualiza tenant_id em benefícios
  (parametrizado, não específico de um documento).
- `import_benefits_to_firestore.py` / `import_partners_to_firestore.py` —
  importam benefícios/parceiros de um JSON para o Firestore (reutilizável
  para reseed).
- `reset_circuit_breaker.py` — reseta o circuit breaker Firestore↔PostgreSQL.
- `setup_cleanup_scheduler.py` — configura o agendador de limpeza.
- `split_firestore_export.py` — divide um export grande do Firestore em
  arquivos menores.
- `sync_users_collection.py` — sincroniza a coleção de usuários com Firebase
  Auth.
- `temp_create_user_and_send_email.py` — cria usuário e envia e-mail de
  boas-vindas (senha temporária).
- `test_firebase_connection.py` — smoke test de conectividade Firebase.
- `validate_artifacts.py` / `validate_student_names.py` — validações de
  integridade.
- `verify_employees_upload.py` / `verify_users_collection.py` — verificação
  pós-upload/sincronização.

## `examples/`

Exemplos autocontidos e simplificados (ver nota em `testing/` sobre as 3
sobreposições de nome com `testing/e2e/`):

- `base_auth_test.py`, `quick_admin_test.py`, `quick_student_test.py` —
  versões simplificadas do fluxo de autenticação/teste rápido.
- `multi_database_example.py` — exemplo de uso do suporte a múltiplos
  bancos Firestore nomeados (`FIRESTORE_DATABASES_LIST`).
- `student_api_ref.py` / `users_api_ref.py` — referência rápida de chamadas
  à API de aluno/usuários.

## Scripts na raiz de `scripts/`

- `run_server.py` — inicia o servidor FastAPI local (usado por
  `python scripts/run_server.py`, ver `CLAUDE.md`).
- `__init__.py` — torna `scripts/` um pacote Python (necessário para os
  imports relativos entre os scripts).

## Uso

```bash
# Diagnóstico
python scripts/debug/check_tenant.py

# Setup de ambiente
python scripts/development/seed_dev.py

# Suíte de testes
python scripts/testing/run_all_tests.py
python scripts/testing/e2e/complete_auth_flow_test.py

# Manutenção (reexecutável)
python scripts/maintenance/courses_operations.py check

# Migração (histórico — não reexecutar sem revisar o estado atual dos dados)
python scripts/migration/fix_document_tenant.py

# Exemplo de referência
python scripts/examples/quick_admin_test.py
```

## Gitignore

Arquivos com prefixo `temp_*.py` e `test_*.py` (mesmo fora de qualquer pasta
`temp/`, que não existe mais) são ignorados pelo Git por padrão — isso
significa que um arquivo novo com esses nomes não aparece em `git status`
até ser adicionado explicitamente com `git add -f`, o que já causou
divergências entre o que a spec desta stage assumia e o estado real do
disco (ver `report.md`). Ao criar um script novo que deve ser versionado,
evitar esses prefixos ou usar `git add -f` conscientemente.
