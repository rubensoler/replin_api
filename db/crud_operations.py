"""
Operaciones CRUD específicas para cargos, personas y actividades.
"""
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from datetime import date

from db.crud import CRUDBase
from models.operations import (
    Cargo, Persona, Actividad,
    ActividadCreate, ActividadUpdate, ActividadRead, ActividadDetallada
)
from models.equipment import Equipo

# CRUD para Cargo
class CRUDCargo(CRUDBase[Cargo, Cargo, Cargo, Cargo]):
    """Operaciones CRUD específicas para el modelo Cargo"""
    
    def get_with_personas(self, session: Session, id: int) -> Optional[Cargo]:
        """
        Obtiene un cargo con las personas que lo tienen asignado
        
        Args:
            session: Sesión de base de datos
            id: ID del cargo
            
        Returns:
            Cargo con personas o None
        """
        query = select(Cargo).where(Cargo.id == id)
        query = query.options(joinedload(Cargo.personas))
        return session.exec(query).first()

# CRUD para Persona
class CRUDPersona(CRUDBase[Persona, Persona, Persona, Persona]):
    """Operaciones CRUD específicas para el modelo Persona"""
    
    def get_with_actividades(self, session: Session, identificacion: int) -> Optional[Persona]:
        """
        Obtiene una persona con sus actividades cargadas
        
        Args:
            session: Sesión de base de datos
            identificacion: Identificación de la persona
            
        Returns:
            Persona con actividades o None
        """
        query = select(Persona).where(Persona.identificacion == identificacion)
        query = query.options(joinedload(Persona.actividades))
        return session.exec(query).first()
    
    def get_by_cargo(self, session: Session, cargo_id: int) -> List[Persona]:
        """
        Lista todas las personas con un cargo específico
        
        Args:
            session: Sesión de base de datos
            cargo_id: ID del cargo
            
        Returns:
            Lista de personas con el cargo
        """
        query = select(Persona).where(Persona.cargo_id == cargo_id)
        return session.exec(query).all()
    
    def get_with_cargo(self, session: Session, identificacion: int) -> Optional[Persona]:
        """
        Obtiene una persona con su cargo cargado
        
        Args:
            session: Sesión de base de datos
            identificacion: Identificación de la persona
            
        Returns:
            Persona con cargo o None
        """
        query = select(Persona).where(Persona.identificacion == identificacion)
        query = query.options(joinedload(Persona.cargo))
        return session.exec(query).first()

# CRUD para Actividad
class CRUDActividad(CRUDBase[Actividad, ActividadCreate, ActividadUpdate, ActividadRead]):
    """Operaciones CRUD específicas para el modelo Actividad"""
    
    def get_with_relations(self, session: Session, id: int) -> Optional[Actividad]:
        """
        Obtiene una actividad con todas sus relaciones cargadas
        
        Args:
            session: Sesión de base de datos
            id: ID de la actividad
            
        Returns:
            Actividad con todas sus relaciones cargadas o None
        """
        query = select(Actividad).where(Actividad.id == id)
        query = query.options(
            joinedload(Actividad.persona).joinedload(Persona.cargo),
            joinedload(Actividad.equipo)
        )
        return session.exec(query).first()
    
    def get_by_persona(self, session: Session, persona_id: int) -> List[Actividad]:
        """
        Lista todas las actividades de una persona específica
        
        Args:
            session: Sesión de base de datos
            persona_id: ID de la persona
            
        Returns:
            Lista de actividades de la persona
        """
        query = select(Actividad).where(Actividad.persona_id == persona_id)
        return session.exec(query).all()
    
    def get_by_equipo(self, session: Session, equipo_id: int) -> List[Actividad]:
        """
        Lista todas las actividades de un equipo específico
        
        Args:
            session: Sesión de base de datos
            equipo_id: ID del equipo
            
        Returns:
            Lista de actividades del equipo
        """
        query = select(Actividad).where(Actividad.equipo_id == equipo_id)
        return session.exec(query).all()
    
    def get_by_fecha(self, session: Session, fecha_inicio: date, fecha_fin: date = None) -> List[Actividad]:
        """
        Lista actividades entre un rango de fechas
        
        Args:
            session: Sesión de base de datos
            fecha_inicio: Fecha inicial
            fecha_fin: Fecha final (opcional, si no se proporciona, se busca por fecha exacta)
            
        Returns:
            Lista de actividades en el rango de fechas
        """
        if fecha_fin:
            query = select(Actividad).where(
                Actividad.fecha >= fecha_inicio,
                Actividad.fecha <= fecha_fin
            )
        else:
            query = select(Actividad).where(Actividad.fecha == fecha_inicio)
            
        return session.exec(query).all()
    
    def get_detalladas(
        self, 
        session: Session, 
        desde: Optional[date] = None,
        hasta: Optional[date] = None,
        persona_id: Optional[int] = None,
        equipo_id: Optional[int] = None
    ) -> List[ActividadDetallada]:
        """
        Obtiene actividades con detalles para visualización filtradas opcionalmente
        
        Args:
            session: Sesión de base de datos
            desde: Fecha inicial opcional
            hasta: Fecha final opcional
            persona_id: ID de persona opcional
            equipo_id: ID de equipo opcional
            
        Returns:
            Lista de actividades detalladas que cumplen con los filtros
        """
        stmt = select(Actividad).options(
            joinedload(Actividad.persona).joinedload(Persona.cargo),
            joinedload(Actividad.equipo)
        )
        
        if desde:
            stmt = stmt.where(Actividad.fecha >= desde)
        if hasta:
            stmt = stmt.where(Actividad.fecha <= hasta)
        if persona_id:
            stmt = stmt.where(Actividad.persona_id == persona_id)
        if equipo_id:
            stmt = stmt.where(Actividad.equipo_id == equipo_id)

        actividades = session.exec(stmt).all()

        resultado = []
        for act in actividades:
            resultado.append(ActividadDetallada(
                id=act.id,
                fecha=act.fecha,
                descripcion=act.descripcion,
                persona=act.persona.nombres,
                cargo=act.persona.cargo.descripcion if act.persona.cargo else None,
                equipo=act.equipo.nombre
            ))
        return resultado

# Instancias CRUD para los modelos
crud_cargo = CRUDCargo(Cargo)
crud_persona = CRUDPersona(Persona)
crud_actividad = CRUDActividad(Actividad)