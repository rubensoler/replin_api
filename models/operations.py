"""
Modelos relacionados con operaciones: cargos, personas y actividades.
"""
from typing import Optional, List
from datetime import date
from sqlmodel import SQLModel, Field, Relationship

# ----------------- CARGOS Y PERSONAS -----------------

class Cargo(SQLModel, table=True):
    """Modelo para cargos laborales"""
    id: Optional[int] = Field(default=None, primary_key=True)
    descripcion: str = Field(max_length=50)
    personas: List["Persona"] = Relationship(back_populates="cargo")

class Persona(SQLModel, table=True):
    """Modelo para personas/empleados"""
    identificacion: int = Field(primary_key=True)
    nombres: str = Field(max_length=100)
    cargo_id: Optional[int] = Field(default=None, foreign_key="cargo.id")
    cargo: Optional[Cargo] = Relationship(back_populates="personas")
    actividades: List["Actividad"] = Relationship(back_populates="persona")

# ----------------- ACTIVIDADES -----------------

class ActividadBase(SQLModel):
    """Modelo base para actividades"""
    descripcion: str = Field(max_length=40, description="Máximo 40 caracteres")
    fecha: date

class Actividad(ActividadBase, table=True):
    """Modelo para actividades de mantenimiento"""
    id: Optional[int] = Field(default=None, primary_key=True)
    equipo_id: int = Field(foreign_key="equipo.id")
    persona_id: int = Field(foreign_key="persona.identificacion")
    equipo: Optional["Equipo"] = Relationship(back_populates="actividades")
    persona: Optional[Persona] = Relationship(back_populates="actividades")

class ActividadCreate(ActividadBase):
    """Modelo para crear una actividad"""
    equipo_id: int
    persona_id: int

class ActividadUpdate(SQLModel):
    """Modelo para actualizar una actividad"""
    descripcion: Optional[str] = Field(default=None, max_length=40)
    fecha: Optional[date] = None
    equipo_id: Optional[int] = None
    persona_id: Optional[int] = None

class ActividadRead(ActividadBase):
    """Modelo básico para leer una actividad"""
    id: int
    equipo_id: int
    persona_id: int

class ActividadDetallada(SQLModel):
    """Modelo para mostrar actividad con información relacionada"""
    id: int
    fecha: date
    descripcion: str
    persona: str
    cargo: Optional[str]
    equipo: str

# Importaciones circulares
from .equipment import Equipo