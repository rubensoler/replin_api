"""
Modelos relacionados con usuarios, roles y aplicaciones.
"""
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# ----------------- USUARIOS Y AUTENTICACIÓN -----------------

class Rol(SQLModel, table=True):
    """Modelo para roles de usuario"""
    id: Optional[int] = Field(default=None, primary_key=True)
    descripcion: str
    usuarios: List["Usuario"] = Relationship(back_populates="rol")
    aplicaciones: List["AplicacionRol"] = Relationship(back_populates="rol")

class Aplicacion(SQLModel, table=True):
    """Modelo para aplicaciones del sistema"""
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    roles: List["AplicacionRol"] = Relationship(back_populates="aplicacion")

class AplicacionRol(SQLModel, table=True):
    """Modelo de tabla intermedia para relación roles-aplicaciones"""
    id: Optional[int] = Field(default=None, primary_key=True)
    rol_id: int = Field(foreign_key="rol.id")
    aplicacion_id: int = Field(foreign_key="aplicacion.id")
    rol: Rol = Relationship(back_populates="aplicaciones")
    aplicacion: Aplicacion = Relationship(back_populates="roles")

class Usuario(SQLModel, table=True):
    """Modelo para usuarios del sistema"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str
    email: Optional[str] = None
    rol_id: int = Field(foreign_key="rol.id")
    rol: Rol = Relationship(back_populates="usuarios")
    contratos: List["ContratoUsuario"] = Relationship(back_populates="usuario")

# Importaciones circulares
from .business import ContratoUsuario