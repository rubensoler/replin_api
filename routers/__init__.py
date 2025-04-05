"""
Paquete de routers para la aplicación GAME.
Este paquete contiene todos los routers de FastAPI organizados por funcionalidad.
"""

# Exportar routers para su uso en main.py
from .equipment import router as equipment_router
from .organization import router as organization_router
from .operations import router as operations_router
from .business import router as business_router
from .users import router as users_router
from .llamaindex import router as llamaindex_router