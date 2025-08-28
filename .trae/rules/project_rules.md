# Project Rules

1. Validate Python files linting with Ruff
2. Validate MD files linting with Markdownlint

## Regras de Validação para Atributos de Alunos

### Atributos Obrigatórios

- `id`: Identificador único do aluno (formato: STD_XXXXXXXX_XX)
- `nome_aluno`: Nome completo do aluno
- `curso`: Curso atual (ex: SEEDS 1, KIDS 2, TEENS 3, TWEENS 4, ADVANCED 1, KINDER 6A)
- `active_until`: Data de validade da matrícula

### Atributos Opcionais

- `ocupacao_aluno`: Ocupação/profissão do aluno
- `email_aluno`: Email do aluno (deve ser um email válido quando preenchido)
- `celular_aluno`: Telefone celular do aluno (formato brasileiro)
- `cep_aluno`: CEP do endereço do aluno (formato: XXXXX-XXX)
- `bairro`: Bairro do endereço do aluno
- `complemento_aluno`: Complemento do endereço (apartamento, casa, etc.)
- `nome_responsavel`: Nome do responsável (obrigatório para menores)
- `email_responsavel`: Email do responsável (deve ser um email válido quando preenchido)

### Regras de Negócio

- Para alunos menores de idade, `nome_responsavel` deve ser preenchido
- Emails devem seguir formato válido quando preenchidos
- CEP deve seguir formato brasileiro (XXXXX-XXX) quando preenchido
- Telefones devem seguir formato brasileiro quando preenchidos
- O campo `curso` deve corresponder aos cursos oferecidos pela escola
