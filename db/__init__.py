"""
Paquete de base de datos para la aplicación GAME.
Este paquete contiene la configuración de la base de datos y operaciones CRUD.
"""

# Exportar la configuración de base de datos
from .database import engine, create_db, get_session

# Exportar la clase base CRUD
from .crud import CRUDBase

# Exportar instancias CRUD para uso directo
from .crud_equipment import crud_equipo, crud_tipo_activo, crud_fabricante, crud_modelo
from .crud_organization import crud_planta, crud_sistema, crud_subsistema
from .crud_operations import crud_cargo, crud_persona, crud_actividad
from .crud_business import crud_cliente, crud_contrato, crud_contrato_usuario
from .crud_users import crud_usuario, crud_rol, crud_aplicacion, crud_aplicacion_rol