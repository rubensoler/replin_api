"""
Modelos relacionados con entidades de negocio: clientes y contratos.
"""
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# ----------------- CONTRATOS Y CLIENTES -----------------

class Cliente(SQLModel, table=True):
    """Modelo para clientes"""
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    contratos: List["Contrato"] = Relationship(back_populates="cliente")

class Contrato(SQLModel, table=True):
    """Modelo para contratos"""
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    cliente_id: int = Field(foreign_key="cliente.id")
    cliente: Cliente = Relationship(back_populates="contratos")
    plantas: List["Planta"] = Relationship(back_populates="contrato")
    contratos_usuarios: List["ContratoUsuario"] = Relationship(back_populates="contrato")

class ContratoUsuario(SQLModel, table=True):
    """Modelo de relación entre contratos y usuarios"""
    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
    contrato_id: int = Field(foreign_key="contrato.id", primary_key=True)
    usuario: "Usuario" = Relationship(back_populates="contratos")
    contrato: Contrato = Relationship(back_populates="contratos_usuarios")

# Importaciones circulares
from .organization import Planta
from .users import Usuario