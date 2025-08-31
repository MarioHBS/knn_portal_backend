"""
Atualização do arquivo principal para integrar todos os componentes.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api import router
from src.config import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    CORS_ORIGINS,
    DEBUG,
    MODE,
    TESTING_MODE,
)
from src.utils import configure_logging, limiter, logger

# Configurar logging
configure_logging()

# Criar aplicação FastAPI
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url=f"/{API_VERSION}/docs",
    redoc_url=f"/{API_VERSION}/redoc",
    openapi_url=f"/{API_VERSION}/openapi.json",
    debug=DEBUG,
)

# Adicionar middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requisições."""
    # Log da requisição
    logger.info(
        "request_started",
        method=request.method,
        url=str(request.url),
        client=request.client.host if request.client else None,
    )

    # Processar requisição
    try:
        response = await call_next(request)

        # Log da resposta
        logger.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
        )

        return response
    except Exception as e:
        # Log de erro
        logger.error(
            "request_failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
        )

        # Retornar erro 500 em caso de exceção não tratada
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {"code": "SERVER_ERROR", "msg": "Erro interno do servidor"}
            },
        )


# Endpoint de health check
@app.get(f"/{API_VERSION}/health")
async def health_check():
    """Endpoint para verificar o status da API."""
    return {"status": "ok", "mode": MODE}


# Incluir todas as rotas da API
app.include_router(router, prefix=f"/{API_VERSION}")


# Manipulador de exceções para erros 404
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Manipulador para rotas não encontradas."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": {"code": "NOT_FOUND", "msg": "Recurso não encontrado"}},
    )


# Manipulador de exceções para erros 422
@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    """Manipulador para erros de validação."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "VALIDATION_ERROR", "msg": "Dados inválidos"}},
    )


# Middleware para injetar tenant_id do JWT
# Imports removidos - não são mais necessários


@app.middleware("http")
async def with_tenant(request: Request, call_next):
    # Pular autenticação para rotas de documentação e health check
    excluded_paths = [
        f"/{API_VERSION}/docs",
        f"/{API_VERSION}/redoc", 
        f"/{API_VERSION}/openapi.json",
        f"/{API_VERSION}/health",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]
    
    if request.url.path in excluded_paths or request.url.path.startswith("/static"):
        return await call_next(request)
    
    # Se estiver em modo de teste, pular autenticação
    if TESTING_MODE:
        # Adicionar tenant_id mock para modo de teste
        request.state.tenant = "test-tenant"
        return await call_next(request)
    
    # Extrai o token Bearer
    authorization: str = request.headers.get("authorization")
    if not authorization or not authorization.lower().startswith("bearer "):
        return JSONResponse(
            status_code=400, content={"error": {"msg": "Token JWT ausente"}}
        )
    token = authorization.split(" ", 1)[1]
    try:
        # Usar a função de verificação do Firebase
        from src.auth import verify_token
        payload = await verify_token(token)
        tenant = payload.tenant
        if not tenant:
            return JSONResponse(
                status_code=400, content={"error": {"msg": "tenant missing"}}
            )
        request.state.tenant = tenant
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": {"msg": "JWT inválido"}})
    return await call_next(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=DEBUG)
