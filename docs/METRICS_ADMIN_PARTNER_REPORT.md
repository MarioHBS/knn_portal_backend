# Relatório de Métricas: Administrador e Parceiro

## Objetivo

Este relatório define o catálogo de métricas do sistema para os perfis Administrador e Parceiro, bem como o plano de implementação para exposição, persistência histórica e filtragem eficiente. Todas as métricas devem considerar timezone Brasília (America/Sao_Paulo) para exibição e campos "last_updated".

## Perfis com métricas persistidas

- Administrador: visão global por tenant (empresa), com possibilidade de filtros por parceiro, benefício, categoria, status e janelas de tempo.
- Parceiro: visão específica por partner_id, com foco em resgates, desempenho de benefícios e engajamento dos usuários vinculados aos seus benefícios.

## Catálogo Final de Métricas

### Observações importantes

- Removidas do catálogo do Admin, conforme solicitação: "novos_7d", "novos_30d", "pendentes_total", "tempo_médio_resgate", "taxa_conversão_benefício".
- Métricas removidas podem ser derivadas via filtragem/séries históricas quando necessário.

### Domínio Usuários (Admin)

- users.ativos: Número de usuários ativos (students com active_until >= hoje).
- users.taxa_crescimento: Percentual de crescimento baseado em período selecionado (derivado dos novos usuários na janela, sem armazenar "novos_7d/30d").
- users.retenção_30d: Percentual de usuários que permaneceram ativos após 30 dias (se disponível; pode ser derivado de eventos).

### Domínio Códigos (Admin)

- codes.gerados_total: Total de códigos de validação gerados no tenant.
- codes.resgatados_total: Total de códigos de validação usados/resgatados.
- codes.taxa_resgate: (resgatados_total / gerados_total) * 100.

### Domínio Parceiros (Admin)

- partners.parceiros_ativos: Total de parceiros ativos.
- partners.resgates_por_parceiro: Contagem de resgates agrupada por partner_id.
- partners.top_parceiros: Ranking de parceiros por volume de resgates.
- partners.taxa_conversão_parceiro: Percentual de códigos gerados que foram resgatados para aquele parceiro (se aplicável aos fluxos).

### Domínio Benefícios (Admin)

- benefits.benefícios_ativos: Total de benefícios ativos (status ativo, dentro da validade).
- benefits.expirando_7d: Total de benefícios com validade encerrando em 7 dias.
- benefits.resgates_por_benefício: Contagem de resgates agrupada por benefit_id.

### Domínio Performance (Admin)

- perf.avg_response_time: Tempo médio de resposta (ms).
- perf.error_rate: Taxa de erro (%).
- perf.uptime: Uptime (%) do backend.
- perf.requests_per_minute: Requisições por minuto.

### Domínio Operacional (Admin)

- meta.contadores_metadata: Estrutura com totals e last_updated para students, employees, partners e benefits.
- meta.last_updated: Última atualização global (BRT) dos contadores.

### Catálogo de Métricas (Parceiro)

Todas filtráveis por partner_id (escopo do parceiro logado):

- partner.codes.gerados_total: Total de códigos vinculados ao parceiro.
- partner.codes.resgatados_total: Total de códigos resgatados do parceiro.
- partner.codes.taxa_resgate: (resgatados_total / gerados_total) * 100.
- partner.benefits.ativos: Total de benefícios ativos do parceiro.
- partner.benefits.expirando_7d: Total de benefícios do parceiro com validade encerrando em 7 dias.
- partner.engajamento.usuarios_impactados: Usuários únicos que resgataram benefícios do parceiro (se aplicável).
- partner.engajamento.resgates_por_benefício: Contagem de resgates por benefit_id do parceiro.
- partner.engajamento.top_benefícios: Ranking de benefícios do parceiro por volume de resgates.

## Estrutura de Dados e Filtragem

### Modelo de Item de Métrica (resposta consolidada)

- key: identificador único (ex.: "users.ativos").
- label: descrição legível (ex.: "Usuários ativos").
- value: valor numérico principal.
- unit: unidade (ex.: "%", "ms", "R$", "count").
- timestamp: ISO com timezone BRT (America/Sao_Paulo) quando aplicável.
- window: janela de agregação ("24h", "7d", "30d", "90d").
- group: agrupamento (ex.: "partner_id" ou "benefit_id").
- dimensions: mapa de dimensões (ex.: {"category": "educação", "status": "active"}).

### Filtros suportados

- Tempo: from, to, granularity (hourly, daily, weekly, monthly).
- Entidade: partner_id, benefit_id, category, status.
- Escopo: tenant_id sempre presente.
- Agregações: group_by (partner_id, benefit_id), top_n (ranking), aggregate (sum, avg, count).
- Paginação/ordenação: limit, offset, order.

## Persistência e Índices

### Coleções Firestore

- metrics_snapshots: snapshots históricos por tenant (e opcionalmente por partner_id/benefit_id), com campos:
  - tenant_id (string)
  - partner_id (string | opcional)
  - benefit_id (string | opcional)
  - domain (string) ex.: "users", "codes", "partners", "benefits", "perf", "meta"
  - key (string) ex.: "users.ativos"
  - value (number)
  - window (string) ex.: "7d"
  - dimensions (map) ex.: {"category": "...", "status": "..."}
  - timestamp (datetime, BRT para leitura/exibição; armazenar UTC no Firestore e converter na API)

- metadata: contadores agregados por-tenant e globais (documentos student_info, employee_info, partner_info, benefit_info) com:
  - total (int)
  - last_updated (string ISO BRT)
  - tenant_id (string | opcional)

- custom_metrics: métricas customizadas para Admin/Parceiro, se aplicável.

### Índices recomendados (Firestore)

- metrics_snapshots: composto (tenant_id ASC, domain ASC, key ASC, timestamp DESC) para ordenação/filtragem temporal.
- metrics_snapshots: composto (tenant_id ASC, partner_id ASC, key ASC, timestamp DESC) para consultas do parceiro.
- metadata: simples por documentId + queries diretas.

## Endpoints e Modelos (Admin)

- GET /admin/metrics/dashboard
  - Retorna dados prontos para UI: resumo, performance, negócio e tendências.

- GET /admin/metrics/historical
  - Parâmetros: start_date, end_date, granularity.
  - Retorna séries temporais por key/domain.

- GET /admin/metrics (unificado)
  - Parâmetros: domain, keys[], from, to, group_by, partner_id, benefit_id, limit, order.
  - Retorna lista de MetricItem com applied_filters.

## Endpoints e Modelos (Parceiro)

- GET /partner/metrics/dashboard
  - Visão consolidada do parceiro (apenas dados do partner_id logado).

- GET /partner/metrics/historical
  - Parâmetros: start_date, end_date, granularity.
  - Séries históricas no escopo do parceiro.

- GET /partner/metrics
  - Parâmetros: keys[], from, to, group_by=benefit_id, limit, order.
  - Responde MetricItem no escopo do partner_id.

## Plano de Implementação

1. Catálogo e modelos
   - Criar catálogo estático (mapa) com keys, labels, units, default_window, groupable.
   - Padronizar Pydantic models para MetricItem e respostas com applied_filters.

2. Serviço de métricas
   - Ajustar MetricsService para utilizar timezone BRT em campos last_updated (já ajustado em update_metadata_on_crud) e normalizar exibição BRT quando necessário.
   - Implementar persistência coerente em metrics_snapshots (armazenar em UTC, converter para BRT na API).
   - Implementar agregações: group_by partner_id/benefit_id, top_n.

3. Endpoints Admin
   - Manter /admin/metrics/dashboard e /admin/metrics/historical.
   - Adicionar /admin/metrics unificado com filtros descritos e retornar lista de MetricItem.
   - Remover do catálogo as métricas descartadas (novos_7d, pendentes_total, tempo_médio_resgate, taxa_conversão_benefício).

4. Endpoints Parceiro
   - Criar /partner/metrics/dashboard e /partner/metrics/historical.
   - Criar /partner/metrics com filtros, escopo por partner_id do JWT.

5. Persistência e índices
   - Configurar índices compostos em Firestore conforme recomendado.
   - Garantir consistência dos documentos metadata por-tenant (prefixo <tenant_id>_doc_name).

6. Testes
   - Adicionar testes de API para endpoints novos (admin e parceiro) cobrindo filtros, group_by e top_n.
   - Validar serialização Pydantic sem objetos Sentinel do Firestore (evitar mutações e usar deepcopy quando necessário na resposta).

7. Observabilidade
   - Rastrear acessos aos endpoints de métricas com analytics_client.
   - Monitorar tempo de resposta e erros dos endpoints e serviço de métricas.

8. Migração/Backfill (opcional)
   - Se necessário, popular metrics_snapshots com dados históricos mínimos para últimos 30 dias.

## Critérios de Aceitação

- Endpoints de Admin e Parceiro disponíveis e documentados.
- Filtros (tempo, entidade, group_by, top_n) funcionando e retornando dados consistentes.
- Contadores metadata exibindo last_updated em BRT.
- Sem erros de serialização (ex.: PydanticSerializationError/Sentinel).
- Índices Firestore criados e consultas com performance aceitável.

## Riscos e Mitigações

- Serialização Firestore (Sentinel/DatetimeWithNanoseconds): usar deepcopy e conversões seguras.
- Divergência de timezone: padronizar armazenamento em UTC e exibição BRT.
- Consulta sem índice: validar índices compostos antes do deploy.

## Referências no Projeto

- src/api/admin_metrics.py — Endpoints avançados de métricas para Admin.
- src/api/admin.py — Endpoint básico /metrics (Admin) e demais rotas.
- src/utils/metrics_service.py — Serviço central de métricas (real-time, snapshots, agregados, BRT em metadata).
- docs/METRICS_IMPLEMENTATION_GUIDE.md — Guia complementar de implementação de métricas.