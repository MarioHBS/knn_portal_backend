"""
Inicialização do pacote de API.
"""
from fastapi import APIRouter

from src.api.admin import router as admin_router
from src.api.employee import router as employee_router
from src.api.partner import router as partner_router
from src.api.student import router as student_router

# Criar router principal
router = APIRouter()

# Incluir routers específicos com prefixos
router.include_router(student_router, prefix="/student")
router.include_router(partner_router, prefix="/partner")
router.include_router(admin_router, prefix="/admin")
router.include_router(employee_router, prefix="/employee")

__all__ = ["router"]
