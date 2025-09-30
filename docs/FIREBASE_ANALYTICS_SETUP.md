# Configuração do Firebase Analytics e Performance

Este documento descreve como configurar e implementar Firebase Analytics e Performance Monitoring no KNN Portal Journey Club Backend.

## Visão Geral

O Firebase Analytics e Performance Monitoring fornecem insights valiosos sobre:

- **Analytics**: Comportamento dos usuários, eventos de negócio, conversões
- **Performance**: Tempo de resposta, latência, throughput, erros

## Configuração Inicial

### 1. Dependências

Adicione as seguintes dependências ao `requirements.txt`:

```txt
firebase-admin==6.6.0
google-cloud-monitoring==2.15.1
google-analytics-data==0.17.4
```

### 2. Configuração do Projeto Firebase

No console do Firebase (https://console.firebase.google.com):

1. Acesse o projeto `knn-benefits`
2. Vá para **Analytics** > **Events**
3. Ative o Google Analytics se ainda não estiver ativo
4. Configure as **Custom Definitions** para eventos personalizados

### 3. Variáveis de Ambiente

Adicione ao arquivo `.env`:

```env
# Firebase Analytics
FIREBASE_ANALYTICS_ENABLED=true
FB_MEASUREMENT_ID=G-XXXXXXXXXX
GOOGLE_ANALYTICS_PROPERTY_ID=123456789

# Performance Monitoring
FIREBASE_PERFORMANCE_ENABLED=true
PERFORMANCE_MONITORING_SAMPLE_RATE=0.1  # 10% das requisições
```

## Estrutura de Dados no Firestore

### Coleções para Analytics

#### 1. `analytics_events`

```json
{
  "event_name": "code_redeemed",
  "timestamp": "2025-01-15T10:30:00Z",
  "tenant_id": "knn-dev-tenant",
  "user_id": "user123",
  "parameters": {
    "code_id": "CODE123",
    "partner_id": "partner456",
    "value": 25.50,
    "currency": "BRL",
    "category": "alimentacao"
  },
  "source": "backend_api",
  "session_id": "session789"
}
```

#### 2. `analytics_metrics`

```json
{
  "metric_name": "total_savings",
  "value": 1250.75,
  "timestamp": "2025-01-15T10:30:00Z",
  "tenant_id": "knn-dev-tenant",
  "additional_data": {
    "period": "monthly",
    "partner_count": 15,
    "user_count": 120
  }
}
```

#### 3. `metrics_snapshots`

```json
{
  "tenant_id": "knn-dev-tenant",
  "timestamp": "2025-01-15T10:30:00Z",
  "metrics": {
    "users": {
      "active_users": 1250,
      "new_users_7d": 45,
      "growth_rate": 3.6
    },
    "codes": {
      "total_codes": 3456,
      "redeemed_codes": 2789,
      "redemption_rate": 80.7
    },
    "partners": {
      "active_partners": 25,
      "avg_redemptions_per_partner": 111.56
    },
    "performance": {
      "avg_response_time": 150,
      "error_rate": 0.5,
      "uptime": 99.9
    }
  }
}
```

#### 4. `custom_metrics`

```json
{
  "tenant_id": "knn-dev-tenant",
  "metric_name": "partner_engagement_score",
  "metric_value": 8.5,
  "metric_type": "gauge",
  "tags": {
    "category": "engagement",
    "partner_type": "premium"
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Eventos Personalizados

### Eventos de Negócio

#### 1. Resgate de Código

```python
await track_code_redemption(
    code_id="CODE123",
    partner_id="partner456",
    user_id="user789",
    tenant_id="knn-dev-tenant",
    value=25.50
)
```

#### 2. Visualização de Parceiro

```python
await track_partner_view(
    partner_id="partner456",
    user_id="user789",
    tenant_id="knn-dev-tenant",
    user_role="student"
)
```

#### 3. Registro de Usuário

```python
await track_user_registration(
    user_id="user789",
    tenant_id="knn-dev-tenant",
    user_role="student",
    registration_method="email"
)
```

### Eventos de Sistema

#### 1. Erro de API

```python
await analytics_client.track_event(
    "api_error",
    {
        "endpoint": "/v1/student/redeem",
        "error_code": "INVALID_CODE",
        "status_code": 400,
        "response_time": 250
    },
    tenant_id=tenant_id
)
```

#### 2. Performance de Endpoint

```python
await analytics_client.track_event(
    "endpoint_performance",
    {
        "endpoint": "/v1/admin/metrics",
        "response_time": 150,
        "status_code": 200,
        "cache_hit": True
    },
    tenant_id=tenant_id
)
```

## Métricas de Performance

### 1. Tempo de Resposta por Endpoint

```python
from src.utils.firebase_analytics import analytics_client

@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time

    # Rastrear performance
    await analytics_client.track_event(
        "endpoint_performance",
        {
            "endpoint": str(request.url.path),
            "method": request.method,
            "response_time": round(process_time * 1000, 2),  # ms
            "status_code": response.status_code
        }
    )

    return response
```

### 2. Métricas de Banco de Dados

```python
async def track_db_performance(operation: str, duration: float, success: bool):
    await analytics_client.track_event(
        "database_operation",
        {
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "success": success,
            "database_type": "firestore"  # ou "postgres"
        }
    )
```

## Dashboard de Métricas

### Endpoint Melhorado

```python
@router.get("/metrics/dashboard", response_model=DashboardResponse)
async def get_dashboard_metrics(
    current_user: JWTPayload = Depends(validate_admin_role),
    period: str = Query("30d", regex="^(1d|7d|30d|90d)$")
):
    """
    Retorna dados completos para dashboard administrativo.
    """
    try:
        from src.utils.metrics_service import metrics_service

        dashboard_data = await metrics_service.generate_dashboard_data(
            current_user.tenant
        )

        return {
            "data": dashboard_data,
            "msg": "ok"
        }

    except Exception as e:
        logger.error(f"Erro ao obter dados do dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "msg": "Erro ao obter métricas"}}
        )
```

## Alertas e Monitoramento

### 1. Alertas Baseados em Métricas

```python
class MetricsAlerts:
    """Sistema de alertas baseado em métricas."""

    async def check_error_rate(self, tenant_id: str) -> None:
        """Verifica taxa de erro e envia alerta se necessário."""
        metrics = await metrics_service.collect_real_time_metrics(tenant_id)
        error_rate = metrics.get("performance", {}).get("error_rate", 0)

        if error_rate > 5.0:  # 5% de erro
            await self.send_alert(
                "high_error_rate",
                f"Taxa de erro alta: {error_rate}%",
                tenant_id
            )

    async def check_response_time(self, tenant_id: str) -> None:
        """Verifica tempo de resposta médio."""
        metrics = await metrics_service.collect_real_time_metrics(tenant_id)
        avg_response = metrics.get("performance", {}).get("avg_response_time", 0)

        if avg_response > 1000:  # 1 segundo
            await self.send_alert(
                "slow_response",
                f"Tempo de resposta alto: {avg_response}ms",
                tenant_id
            )
```

### 2. Relatórios Automáticos

```python
async def generate_daily_report(tenant_id: str) -> Dict[str, Any]:
    """Gera relatório diário de métricas."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=1)

    metrics = await metrics_service.get_historical_metrics(
        tenant_id, start_date, end_date, "hourly"
    )

    report = {
        "date": end_date.date().isoformat(),
        "tenant_id": tenant_id,
        "summary": {
            "total_redemptions": metrics.get("total_redemptions", 0),
            "unique_users": metrics.get("unique_users", 0),
            "avg_response_time": metrics.get("avg_response_time", 0),
            "error_count": metrics.get("error_count", 0)
        },
        "trends": await metrics_service._calculate_trends(tenant_id)
    }

    return report
```

## Índices Firestore Necessários

```json
[
  {
    "collectionGroup": "analytics_events",
    "fields": [
      {"fieldPath": "tenant_id", "order": "ASCENDING"},
      {"fieldPath": "event_name", "order": "ASCENDING"},
      {"fieldPath": "timestamp", "order": "DESCENDING"}
    ]
  },
  {
    "collectionGroup": "metrics_snapshots",
    "fields": [
      {"fieldPath": "tenant_id", "order": "ASCENDING"},
      {"fieldPath": "timestamp", "order": "DESCENDING"}
    ]
  },
  {
    "collectionGroup": "custom_metrics",
    "fields": [
      {"fieldPath": "tenant_id", "order": "ASCENDING"},
      {"fieldPath": "metric_name", "order": "ASCENDING"},
      {"fieldPath": "timestamp", "order": "DESCENDING"}
    ]
  }
]
```

## Implementação Gradual

### Fase 1: Eventos Básicos (Semana 1)
- [x] Configurar Firebase Analytics
- [x] Implementar eventos de resgate de código
- [x] Implementar eventos de visualização de parceiro
- [x] Criar coleções básicas no Firestore

### Fase 2: Métricas Avançadas (Semana 2)
- [ ] Implementar coleta de métricas de performance
- [ ] Criar dashboard administrativo
- [ ] Implementar métricas históricas
- [ ] Configurar alertas básicos

### Fase 3: Analytics Avançado (Semana 3)
- [ ] Implementar funis de conversão
- [ ] Criar segmentação de usuários
- [ ] Implementar A/B testing
- [ ] Relatórios automatizados

### Fase 4: Otimização (Semana 4)
- [ ] Otimizar performance das consultas
- [ ] Implementar cache de métricas
- [ ] Configurar exportação para BigQuery
- [ ] Documentação completa

## Considerações de Performance

### 1. Sampling
- Use sampling para eventos de alta frequência
- Configure taxa de amostragem por tipo de evento
- Implemente sampling adaptativo baseado em carga

### 2. Batch Processing
- Processe eventos em lotes para reduzir latência
- Use filas assíncronas para eventos não críticos
- Implemente retry logic para falhas temporárias

### 3. Caching
- Cache métricas frequentemente acessadas
- Use Redis para cache de métricas em tempo real
- Implemente invalidação inteligente de cache

## Segurança e Privacidade

### 1. Dados Sensíveis
- Nunca rastreie informações pessoais identificáveis
- Use hashing para IDs de usuário quando necessário
- Implemente retenção de dados conforme LGPD

### 2. Controle de Acesso
- Métricas por tenant são isoladas
- Apenas administradores podem acessar métricas completas
- Implemente auditoria de acesso às métricas

## Monitoramento e Alertas

### 1. Métricas do Sistema
- Taxa de erro por endpoint
- Tempo de resposta médio
- Throughput de requisições
- Uso de recursos (CPU, memória)

### 2. Métricas de Negócio
- Taxa de conversão de códigos
- Engajamento de parceiros
- Crescimento de usuários
- Valor total economizado

## Próximos Passos

1. **Implementar eventos básicos** nos endpoints existentes
2. **Configurar dashboard** no frontend administrativo
3. **Testar coleta de métricas** em ambiente de desenvolvimento
4. **Configurar alertas** para métricas críticas
5. **Documentar** uso das métricas para stakeholders

---

**Data de Criação**: 15 de Janeiro de 2025
**Última Atualização**: 15 de Janeiro de 2025
**Versão**: 1.0
**Autor**: Sistema KNN Portal
