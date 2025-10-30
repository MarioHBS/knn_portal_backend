"""
Portal de Benefícios KNN - API Principal.

Esta API permite que alunos da KNN Idiomas acessem promoções exclusivas
de parceiros comerciais através de um sistema de autenticação seguro.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api import (
    admin,
    admin_benefit,
    admin_employee,
    admin_metrics,
    admin_partner,
    admin_student,
    courses,
    employee,
    logos,
    partner,
    student,
    sync,
    users,
)
from src.config import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    CORS_ORIGINS,
    DEBUG,
    ENVIRONMENT,
)
from src.db.firestore import initialize_firestore_databases
from src.db.storage import initialize_storage_client
from src.utils.rate_limit import limiter

# Configurar logging
logging.basicConfig(
    level=logging.INFO if DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup
    logger.info(f"🚀 Iniciando aplicação em modo {ENVIRONMENT}")
    logger.info(f"🔧 Debug mode: {DEBUG}")

    # Inicializar Firestore
    initialize_firestore_databases()

    # Inicializar Storage
    initialize_storage_client()

    logger.info("✅ Aplicação iniciada com sucesso")

    yield

    # Shutdown
    logger.info("🛑 Encerrando aplicação")


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url=f"/{API_VERSION}/docs",
    redoc_url=f"/{API_VERSION}/redoc",
    openapi_url=f"/{API_VERSION}/openapi.json",
)

# Middleware de CORS
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handler para exceções de validação."""
    logger.error(f"Erro de validação: {exc.errors()}", exc_info=True)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# Incluir routers
app.include_router(courses.router, prefix=f"/{API_VERSION}/courses", tags=["Courses"])
app.include_router(admin.router, prefix=f"/{API_VERSION}/admin", tags=["Admin"])
app.include_router(
    admin_benefit.router, prefix=f"/{API_VERSION}/admin", tags=["Admin - Benefits"]
)
app.include_router(
    admin_employee.router, prefix=f"/{API_VERSION}/admin", tags=["Admin - Employees"]
)
app.include_router(
    admin_partner.router, prefix=f"/{API_VERSION}/admin", tags=["Admin - Partners"]
)
app.include_router(
    admin_student.router, prefix=f"/{API_VERSION}/admin", tags=["Admin - Students"]
)

app.include_router(
    admin_metrics.router, prefix=f"/{API_VERSION}", tags=["Admin Metrics"]
)
app.include_router(
    employee.router, prefix=f"/{API_VERSION}/employee", tags=["Employee"]
)
app.include_router(logos.router, prefix=f"/{API_VERSION}/logos", tags=["Logos"])
app.include_router(partner.router, prefix=f"/{API_VERSION}/partner", tags=["Partner"])
app.include_router(student.router, prefix=f"/{API_VERSION}/student", tags=["Student"])
app.include_router(sync.router, prefix=f"/{API_VERSION}/sync", tags=["Sync"])
app.include_router(users.router, prefix=f"/{API_VERSION}/users", tags=["Users"])


@app.get("/")
async def root():
    """Endpoint raiz da API."""
    return {
        "message": "Portal de Benefícios KNN API",
        "version": API_VERSION,
        "environment": ENVIRONMENT,
        "status": "running",
    }


@app.get(f"/{API_VERSION}/health")
async def health_check():
    """Endpoint de verificação de saúde da API."""
    return {"status": "healthy", "environment": ENVIRONMENT}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas."""
    logger.error(f"❌ Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "msg": "Erro interno do servidor",
            }
        },
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=ENVIRONMENT == "development",
    )
