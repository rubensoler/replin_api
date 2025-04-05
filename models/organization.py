"""
Modelos relacionados con la estructura organizativa: plantas, sistemas y subsistemas.
"""
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# Importación anticipada para evitar referencia circular
from .equipment import EquipoReadMini

# ----------------- ESTRUCTURA PLANTA - SISTEMA - SUBSISTEMA -----------------

class Sistema(SQLModel, table=True):
    """Modelo para sistemas"""
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(max_length=20)
    nombre: str
    descripcion: Optional[str] = None 
    planta_id: int = Field(foreign_key="planta.id")

    planta: Optional["Planta"] = Relationship(back_populates="sistemas")
    subsistemas: List["SubSistema"] = Relationship(back_populates="sistema")

class SubSistema(SQLModel, table=True):
    """Modelo para subsistemas"""
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(max_length=20)
    nombre: str
    descripcion: Optional[str] = None 
    sistema_id: int = Field(foreign_key="sistema.id")

    sistema: Optional[Sistema] = Relationship(back_populates="subsistemas")
    equipos: List["Equipo"] = Relationship(back_populates="subsistema")

class Planta(SQLModel, table=True):
    """Modelo para plantas"""
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    municipio: str
    localizacion: Optional[str] = None  # GPS
    contrato_id: int = Field(foreign_key="contrato.id")
    contrato: "Contrato" = Relationship(back_populates="plantas")
    sistemas: List[Sistema] = Relationship(back_populates="planta")

# ----------------- MODELOS JERÁRQUICOS (PARA VISUALIZACIÓN) -----------------

class SubSistemaRead(SQLModel):
    """Modelo de lectura para subsistemas en jerarquía"""
    id: int
    codigo: str
    nombre: str
    descripcion: str 
    equipos: List[EquipoReadMini] = []

class SistemaRead(SQLModel):
    """Modelo de lectura para sistemas en jerarquía"""
    id: int
    codigo: str
    nombre: str
    descripcion: str
    subsistemas: List[SubSistemaRead] = []

class PlantaJerarquica(SQLModel):
    """Modelo de lectura jerárquica completa de planta"""
    id: int
    nombre: str
    municipio: str
    localizacion: Optional[str] = None
    sistemas: List[SistemaRead] = []

# Importaciones circulares que necesitan ser manejadas con strings
from .equipment import Equipo
from .business import Contrato