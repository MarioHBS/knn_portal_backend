"""Portal de Benefícios KNN - Módulo Principal

Este módulo contém a estrutura principal da aplicação backend do Portal de Benefícios.
"""

__version__ = "1.0.0"
__author__ = "KNN Team"

# Importar módulos principais para torná-los disponíveis
from . import api, models, utils

# Exportar módulos para uso externo
__all__ = ["api", "models", "utils"]
