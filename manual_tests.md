"""
Documentação de Testes Manuais para o Portal de Benefícios KNN

Este documento descreve os procedimentos para testes manuais do Portal de Benefícios KNN,
complementando os testes automatizados no script test_endpoints.py.
"""

# Preparação para Testes

1. Inicie o servidor FastAPI:
   ```
   python run_server.py
   ```

2. Acesse a documentação Swagger:
   http://localhost:8080/v1/docs

# Testes Manuais por Perfil

## Testes Gerais

- [ ] Verificar se o endpoint de health check retorna status "ok"
- [ ] Verificar se requisições sem token são rejeitadas com 401
- [ ] Verificar se requisições com token inválido são rejeitadas com 401
- [ ] Verificar se requisições com role incorreta são rejeitadas com 403

## Testes de Perfil Aluno (Student)

- [ ] Listar parceiros (GET /partners)
- [ ] Filtrar parceiros por categoria (GET /partners?cat=Livraria)
- [ ] Ordenar parceiros (GET /partners?ord=name_asc)
- [ ] Ver detalhes de um parceiro (GET /partners/{id})
- [ ] Gerar código de validação (POST /validation-codes)
- [ ] Verificar se o código expira após 3 minutos
- [ ] Ver histórico de resgates (GET /students/me/history)
- [ ] Ver favoritos (GET /students/me/fav)
- [ ] Adicionar parceiro aos favoritos (POST /students/me/fav)
- [ ] Remover parceiro dos favoritos (DELETE /students/me/fav/{pid})

## Testes de Perfil Parceiro (Partner)

- [ ] Resgatar código válido (POST /partner/redeem)
- [ ] Tentar resgatar código inválido (POST /partner/redeem)
- [ ] Tentar resgatar código expirado (POST /partner/redeem)
- [ ] Verificar rate limit (5 requisições por minuto)
- [ ] Listar promoções (GET /partner/promotions)
- [ ] Criar promoção (POST /partner/promotions)
- [ ] Atualizar promoção (PUT /partner/promotions/{id})
- [ ] Desativar promoção (DELETE /partner/promotions/{id})
- [ ] Ver relatório de uso (GET /partner/reports?range=2025-05)

## Testes de Perfil Funcionário (Employee)

- [ ] Listar parceiros (GET /employees/partners)
- [ ] Filtrar parceiros por categoria (GET /employees/partners?cat=Livraria)
- [ ] Ordenar parceiros (GET /employees/partners?ord=name_asc)
- [ ] Ver detalhes de um parceiro (GET /employees/partners/{id})
- [ ] Verificar se promoções são filtradas para funcionários (target_profile=employee ou both)
- [ ] Gerar código de validação (POST /employees/validation-codes)
- [ ] Verificar se o código expira após 3 minutos
- [ ] Ver histórico de resgates (GET /employees/me/history)
- [ ] Ver favoritos (GET /employees/me/fav)
- [ ] Adicionar parceiro aos favoritos (POST /employees/me/fav)
- [ ] Remover parceiro dos favoritos (DELETE /employees/me/fav/{pid})
- [ ] Verificar se funcionário inativo não pode gerar códigos

## Testes de Perfil Administrador (Admin)

- [ ] Listar estudantes (GET /admin/students)
- [ ] Listar parceiros (GET /admin/partners)
- [ ] Listar promoções (GET /admin/promotions)
- [ ] Criar entidade (POST /admin/{entity})
- [ ] Atualizar entidade (PUT /admin/{entity}/{id})
- [ ] Remover/inativar entidade (DELETE /admin/{entity}/{id})
- [ ] Ver métricas do sistema (GET /admin/metrics)
- [ ] Enviar notificações (POST /admin/notifications)

## Testes de Resiliência e Segurança

- [ ] Verificar mascaramento de CPF nos logs
- [ ] Simular falhas no Firestore e verificar fallback para PostgreSQL
- [ ] Verificar ativação do circuit breaker após 3 falhas consecutivas
- [ ] Verificar se o modo degradado é ativado corretamente
- [ ] Verificar se o CORS está restrito aos domínios permitidos

# Tokens JWT para Testes

## Token de Aluno
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50LWlkIiwicm9sZSI6InN0dWRlbnQiLCJleHAiOjE3MTY5OTIwMDAsImlhdCI6MTcxNjkwNTYwMH0.8Uj7hl5vYGnEZQGR5QeQQOdTKB4ZXEfEiqxJxlE5Pjw
```

## Token de Parceiro
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJ0bmVyLWlkIiwicm9sZSI6InBhcnRuZXIiLCJleHAiOjE3MTY5OTIwMDAsImlhdCI6MTcxNjkwNTYwMH0.Hn5Fq5qSVBN5QjuoYd2KBjTIGJJoV9OQh-VzpNqJrSs
```

## Token de Administrador
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbi1pZCIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcxNjk5MjAwMCwiaWF0IjoxNzE2OTA1NjAwfQ.jQyOq0-KnzH0vqBQwKsqzTBGzKqGLYVj9WdAZKbK5Hs
```

# Relatório de Testes

Ao concluir os testes, documente:

1. Quais testes passaram
2. Quais testes falharam e por quê
3. Quaisquer problemas encontrados
4. Sugestões de melhorias
