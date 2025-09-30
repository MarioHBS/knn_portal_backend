"""
Middleware para coleta automática de métricas de performance.

Este middleware intercepta todas as requisições HTTP e coleta métricas
de performance, incluindo tempo de resposta, status codes e erros.
"""

import time
from datetime import datetime
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.firebase_analytics import analytics_client
from src.utils.logger import logger


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware para coleta de métricas de performance.
    
    Coleta automaticamente:
    - Tempo de resposta por endpoint
    - Status codes de resposta
    - Erros e exceções
    - Throughput de requisições
    - Métricas por tenant
    """
    
    def __init__(self, app, sample_rate: float = 1.0):
        """
        Inicializa o middleware de performance.
        
        Args:
            app: Aplicação FastAPI
            sample_rate: Taxa de amostragem (0.0 a 1.0)
        """
        super().__init__(app)
        self.sample_rate = sample_rate
        self.request_count = 0
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa a requisição e coleta métricas de performance.
        
        Args:
            request: Requisição HTTP
            call_next: Próximo middleware/handler
            
        Returns:
            Response: Resposta HTTP
        """
        # Incrementar contador de requisições
        self.request_count += 1
        
        # Aplicar sampling
        should_track = (self.request_count % int(1 / self.sample_rate)) == 0
        
        # Dados básicos da requisição
        start_time = time.time()
        endpoint = str(request.url.path)
        method = request.method
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extrair tenant_id do header ou token
        tenant_id = await self._extract_tenant_id(request)
        
        # Processar requisição
        response = None
        error_occurred = False
        error_type = None
        
        try:
            response = await call_next(request)
            
        except Exception as e:
            error_occurred = True
            error_type = type(e).__name__
            logger.error(f"Erro no endpoint {endpoint}: {str(e)}")
            
            # Re-raise a exceção para não interferir no fluxo
            raise
            
        finally:
            # Calcular tempo de resposta
            process_time = time.time() - start_time
            response_time_ms = round(process_time * 1000, 2)
            
            # Coletar métricas se deve rastrear
            if should_track:
                await self._track_performance_metrics(
                    endpoint=endpoint,
                    method=method,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code if response else 500,
                    error_occurred=error_occurred,
                    error_type=error_type,
                    user_agent=user_agent,
                    tenant_id=tenant_id
                )
        
        # Adicionar headers de performance
        if response:
            response.headers["X-Response-Time"] = str(response_time_ms)
            response.headers["X-Request-ID"] = str(self.request_count)
        
        return response
    
    async def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """
        Extrai o tenant_id da requisição.
        
        Args:
            request: Requisição HTTP
            
        Returns:
            str: Tenant ID ou None se não encontrado
        """
        try:
            # Tentar extrair do header personalizado
            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                return tenant_id
            
            # Tentar extrair do token JWT (se disponível)
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Aqui você pode decodificar o JWT para extrair o tenant_id
                # Por simplicidade, vamos usar um método mock
                # Em produção, use a função de decodificação JWT existente
                pass
            
            # Tentar extrair da URL (para endpoints que incluem tenant)
            path_parts = request.url.path.split("/")
            if len(path_parts) > 2 and path_parts[1] == "tenant":
                return path_parts[2]
            
            return None
            
        except Exception as e:
            logger.warning(f"Erro ao extrair tenant_id: {str(e)}")
            return None
    
    async def _track_performance_metrics(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        error_occurred: bool,
        error_type: Optional[str],
        user_agent: str,
        tenant_id: Optional[str]
    ):
        """
        Rastreia métricas de performance no Firebase Analytics.
        
        Args:
            endpoint: Endpoint da requisição
            method: Método HTTP
            response_time_ms: Tempo de resposta em milissegundos
            status_code: Código de status HTTP
            error_occurred: Se ocorreu erro
            error_type: Tipo do erro (se houver)
            user_agent: User agent do cliente
            tenant_id: ID do tenant
        """
        try:
            # Classificar endpoint (público, admin, student, etc.)
            endpoint_category = self._classify_endpoint(endpoint)
            
            # Classificar performance
            performance_category = self._classify_performance(response_time_ms)
            
            # Evento de performance básico
            await analytics_client.track_event(
                "endpoint_performance",
                {
                    "endpoint": endpoint,
                    "method": method,
                    "response_time": response_time_ms,
                    "status_code": status_code,
                    "endpoint_category": endpoint_category,
                    "performance_category": performance_category,
                    "user_agent_type": self._classify_user_agent(user_agent),
                    "timestamp": datetime.utcnow().isoformat()
                },
                tenant_id=tenant_id
            )
            
            # Evento de erro (se houver)
            if error_occurred:
                await analytics_client.track_event(
                    "endpoint_error",
                    {
                        "endpoint": endpoint,
                        "method": method,
                        "error_type": error_type,
                        "status_code": status_code,
                        "response_time": response_time_ms,
                        "endpoint_category": endpoint_category,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    tenant_id=tenant_id
                )
            
            # Métricas específicas para endpoints críticos
            if endpoint_category in ["admin", "student_auth", "code_redemption"]:
                await analytics_client.track_event(
                    "critical_endpoint_performance",
                    {
                        "endpoint": endpoint,
                        "method": method,
                        "response_time": response_time_ms,
                        "status_code": status_code,
                        "is_slow": response_time_ms > 1000,  # > 1 segundo
                        "is_error": error_occurred,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    tenant_id=tenant_id
                )
            
        except Exception as e:
            # Não falhar a requisição por erro no tracking
            logger.warning(f"Erro ao rastrear métricas de performance: {str(e)}")
    
    def _classify_endpoint(self, endpoint: str) -> str:
        """
        Classifica o endpoint por categoria.
        
        Args:
            endpoint: Path do endpoint
            
        Returns:
            str: Categoria do endpoint
        """
        if "/admin/" in endpoint:
            return "admin"
        elif "/student/" in endpoint:
            return "student"
        elif "/auth/" in endpoint:
            return "auth"
        elif "/redeem" in endpoint or "/code" in endpoint:
            return "code_redemption"
        elif "/partner" in endpoint:
            return "partner"
        elif "/health" in endpoint or "/status" in endpoint:
            return "health"
        elif "/docs" in endpoint or "/openapi" in endpoint:
            return "documentation"
        else:
            return "other"
    
    def _classify_performance(self, response_time_ms: float) -> str:
        """
        Classifica a performance da requisição.
        
        Args:
            response_time_ms: Tempo de resposta em milissegundos
            
        Returns:
            str: Categoria de performance
        """
        if response_time_ms < 100:
            return "excellent"
        elif response_time_ms < 300:
            return "good"
        elif response_time_ms < 1000:
            return "acceptable"
        elif response_time_ms < 3000:
            return "slow"
        else:
            return "very_slow"
    
    def _classify_user_agent(self, user_agent: str) -> str:
        """
        Classifica o user agent por tipo.
        
        Args:
            user_agent: String do user agent
            
        Returns:
            str: Tipo do user agent
        """
        user_agent_lower = user_agent.lower()
        
        if "mobile" in user_agent_lower or "android" in user_agent_lower or "iphone" in user_agent_lower:
            return "mobile"
        elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
            return "tablet"
        elif "bot" in user_agent_lower or "crawler" in user_agent_lower or "spider" in user_agent_lower:
            return "bot"
        elif "postman" in user_agent_lower or "insomnia" in user_agent_lower or "curl" in user_agent_lower:
            return "api_client"
        elif "chrome" in user_agent_lower or "firefox" in user_agent_lower or "safari" in user_agent_lower:
            return "desktop_browser"
        else:
            return "unknown"


class DatabasePerformanceTracker:
    """
    Tracker para métricas de performance de banco de dados.
    
    Pode ser usado como context manager para rastrear operações de banco.
    """
    
    def __init__(self, operation: str, database_type: str, tenant_id: Optional[str] = None):
        """
        Inicializa o tracker de performance de banco.
        
        Args:
            operation: Nome da operação (select, insert, update, delete)
            database_type: Tipo do banco (firestore, postgres)
            tenant_id: ID do tenant
        """
        self.operation = operation
        self.database_type = database_type
        self.tenant_id = tenant_id
        self.start_time = None
        self.success = True
        self.error_type = None
    
    async def __aenter__(self):
        """Inicia o tracking da operação."""
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Finaliza o tracking e envia métricas."""
        if exc_type is not None:
            self.success = False
            self.error_type = exc_type.__name__
        
        duration_ms = round((time.time() - self.start_time) * 1000, 2)
        
        try:
            await analytics_client.track_event(
                "database_operation",
                {
                    "operation": self.operation,
                    "database_type": self.database_type,
                    "duration_ms": duration_ms,
                    "success": self.success,
                    "error_type": self.error_type,
                    "timestamp": datetime.utcnow().isoformat()
                },
                tenant_id=self.tenant_id
            )
        except Exception as e:
            logger.warning(f"Erro ao rastrear performance do banco: {str(e)}")


# Funções utilitárias para uso em outros módulos

async def track_database_operation(
    operation: str,
    database_type: str,
    duration_ms: float,
    success: bool = True,
    error_type: Optional[str] = None,
    tenant_id: Optional[str] = None
):
    """
    Rastreia uma operação de banco de dados.
    
    Args:
        operation: Nome da operação
        database_type: Tipo do banco
        duration_ms: Duração em milissegundos
        success: Se a operação foi bem-sucedida
        error_type: Tipo do erro (se houver)
        tenant_id: ID do tenant
    """
    try:
        await analytics_client.track_event(
            "database_operation",
            {
                "operation": operation,
                "database_type": database_type,
                "duration_ms": duration_ms,
                "success": success,
                "error_type": error_type,
                "timestamp": datetime.utcnow().isoformat()
            },
            tenant_id=tenant_id
        )
    except Exception as e:
        logger.warning(f"Erro ao rastrear operação de banco: {str(e)}")


async def track_cache_operation(
    operation: str,
    cache_type: str,
    hit: bool,
    duration_ms: float,
    tenant_id: Optional[str] = None
):
    """
    Rastreia uma operação de cache.
    
    Args:
        operation: Tipo de operação (get, set, delete)
        cache_type: Tipo do cache (redis, memory)
        hit: Se foi cache hit ou miss
        duration_ms: Duração em milissegundos
        tenant_id: ID do tenant
    """
    try:
        await analytics_client.track_event(
            "cache_operation",
            {
                "operation": operation,
                "cache_type": cache_type,
                "hit": hit,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat()
            },
            tenant_id=tenant_id
        )
    except Exception as e:
        logger.warning(f"Erro ao rastrear operação de cache: {str(e)}")


async def track_external_api_call(
    api_name: str,
    endpoint: str,
    method: str,
    response_time_ms: float,
    status_code: int,
    success: bool,
    tenant_id: Optional[str] = None
):
    """
    Rastreia uma chamada para API externa.
    
    Args:
        api_name: Nome da API externa
        endpoint: Endpoint chamado
        method: Método HTTP
        response_time_ms: Tempo de resposta
        status_code: Código de status
        success: Se a chamada foi bem-sucedida
        tenant_id: ID do tenant
    """
    try:
        await analytics_client.track_event(
            "external_api_call",
            {
                "api_name": api_name,
                "endpoint": endpoint,
                "method": method,
                "response_time": response_time_ms,
                "status_code": status_code,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            },
            tenant_id=tenant_id
        )
    except Exception as e:
        logger.warning(f"Erro ao rastrear chamada de API externa: {str(e)}")