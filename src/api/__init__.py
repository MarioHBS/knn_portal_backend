"""
Inicialização do pacote de API.
"""

from fastapi import APIRouter

from src.api.admin import router as admin_router
from src.api.employee import router as employee_router
from src.api.partner import router as partner_router
from src.api.student import router as student_router
from src.api.users import router as users_router
from src.api.utils import router as utils_router

# Criar router principal
router = APIRouter()

# Incluir routers específicos com prefixos
router.include_router(users_router, prefix="/users")
router.include_router(student_router, prefix="/student")
router.include_router(partner_router, prefix="/partner")
router.include_router(admin_router, prefix="/admin")
router.include_router(employee_router, prefix="/employee")
router.include_router(utils_router, prefix="/utils")

__all__ = ["router"]
