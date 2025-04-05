"""
Modelos relacionados con equipos, tipos de activos, fabricantes y modelos.
"""
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# ----------------- TIPO DE ACTIVOS -----------------
class TipoActivoBase(SQLModel):
    """Modelo base para tipos de activos"""
    descripcion: str
    imagen: Optional[str] = None

class TipoActivo(TipoActivoBase, table=True):
    """Modelo de tipo de activo para la base de datos"""
    id: Optional[int] = Field(default=None, primary_key=True)

class TipoActivoCreate(TipoActivoBase):
    """Modelo para crear un tipo de activo"""
    pass

class TipoActivoRead(TipoActivoBase):
    """Modelo para leer un tipo de activo"""
    id: int

class TipoActivoUpdate(SQLModel):
    """Modelo para actualizar un tipo de activo"""
    descripcion: Optional[str] = None
    imagen: Optional[str] = None

# ----------------- FABRICANTE Y MODELO -----------------

class FabricanteBase(SQLModel):
    """Modelo base para fabricantes"""
    nombre: str = Field(max_length=100)

class Fabricante(FabricanteBase, table=True):
    """Modelo de fabricante para la base de datos"""
    id: Optional[int] = Field(default=None, primary_key=True)
    modelos: List["Modelo"] = Relationship(back_populates="fabricante")

class FabricanteCreate(FabricanteBase):
    """Modelo para crear un fabricante"""
    pass

class FabricanteRead(FabricanteBase):
    """Modelo para leer un fabricante"""
    id: int

class FabricanteUpdate(SQLModel):
    """Modelo para actualizar un fabricante"""
    nombre: Optional[str] = None

class ModeloBase(SQLModel):
    """Modelo base para modelos de equipos"""
    nombre: str = Field(max_length=100)

class Modelo(ModeloBase, table=True):
    """Modelo de modelo de equipo para la base de datos"""
    id: Optional[int] = Field(default=None, primary_key=True)
    fabricante_id: int = Field(foreign_key="fabricante.id")
    fabricante: Optional[Fabricante] = Relationship(back_populates="modelos")
    equipos: List["Equipo"] = Relationship(back_populates="modelo")

class ModeloCreate(ModeloBase):
    """Modelo para crear un modelo de equipo"""
    fabricante_id: int

class ModeloRead(ModeloBase):
    """Modelo para leer un modelo de equipo"""
    id: int
    fabricante_id: int

class ModeloReadDetallado(ModeloBase):
    """Modelo para leer un modelo de equipo con detalles del fabricante"""
    id: int
    fabricante_id: int
    fabricante: Optional[FabricanteRead]

class ModeloUpdate(SQLModel):
    """Modelo para actualizar un modelo de equipo"""
    nombre: Optional[str] = None
    fabricante_id: Optional[int] = None

# ----------------- EQUIPOS -----------------
class EquipoBase(SQLModel):
    """Modelo base para equipos"""
    nombre: str
    ubicacion: Optional[str] = None
    imagen: Optional[str] = Field(default=None, max_length=20, description="Nombre del archivo de imagen")

class Equipo(EquipoBase, table=True):
    """Modelo de equipo para la base de datos"""
    id: Optional[int] = Field(default=None, primary_key=True)
    subsistema_id: int = Field(foreign_key="subsistema.id")
    tipo_activo_id: int = Field(foreign_key="tipoactivo.id")
    fabricante_id: Optional[int] = Field(default=None, foreign_key="fabricante.id")
    modelo_id: Optional[int] = Field(default=None, foreign_key="modelo.id")

    actividades: List["Actividad"] = Relationship(back_populates="equipo")
    subsistema: Optional["SubSistema"] = Relationship(back_populates="equipos")
    tipo_activo: Optional[TipoActivo] = Relationship()
    fabricante: Optional[Fabricante] = Relationship()
    modelo: Optional[Modelo] = Relationship(back_populates="equipos")

class EquipoReadDetallado(SQLModel):
    """Modelo para leer un equipo con todos sus detalles"""
    id: int
    nombre: str
    ubicacion: Optional[str]
    imagen: Optional[str]
    subsistema_id: int
    tipo_activo_id: int
    fabricante_id: Optional[int]
    modelo_id: Optional[int]
    subsistema: Optional["SubSistema"]
    tipo_activo: Optional[TipoActivo]
    fabricante: Optional[Fabricante]
    modelo: Optional[Modelo]

class EquipoCreate(EquipoBase):
    """Modelo para crear un equipo"""
    subsistema_id: int
    tipo_activo_id: int
    fabricante_id: Optional[int] = None
    modelo_id: Optional[int] = None

class EquipoUpdate(SQLModel):
    """Modelo para actualizar un equipo"""
    nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    imagen: Optional[str] = Field(default=None, max_length=20)
    subsistema_id: Optional[int] = None
    tipo_activo_id: Optional[int] = None
    fabricante_id: Optional[int] = None
    modelo_id: Optional[int] = None

class EquipoRead(EquipoBase):
    """Modelo para leer un equipo básico"""
    id: int

class EquipoReadMini(SQLModel):
    """Modelo para leer un equipo mini para la jerarquía"""
    id: int
    nombre: str

# Importaciones circulares que necesitan ser manejadas con strings
from .organization import SubSistema
from .operations import Actividad