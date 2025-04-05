"""
Modelos para la aplicación GAME.
Este paquete contiene todas las definiciones de modelos SQLModel
para la base de datos de la aplicación.
"""

# Importar todos los modelos para que estén disponibles desde models
from .equipment import *
from .organization import *
from .users import *
from .business import *
from .operations import *

# Para crear tablas en la base de datos
from sqlmodel import SQLModel