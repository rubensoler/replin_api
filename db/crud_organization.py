"""
Operaciones CRUD específicas para plantas, sistemas y subsistemas.
"""
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select

from db.crud import CRUDBase
from models.organization import (
    Planta, Sistema, SubSistema,
    PlantaJerarquica, SistemaRead, SubSistemaRead
)
from models.business import Contrato
from models.equipment import Equipo

# CRUD para Planta
class CRUDPlanta(CRUDBase[Planta, Planta, Planta, Planta]):
    """Operaciones CRUD específicas para el modelo Planta"""
    
    def get_with_sistemas(self, session: Session, id: int) -> Optional[Planta]:
        """
        Obtiene una planta con sus sistemas cargados
        
        Args:
            session: Sesión de base de datos
            id: ID de la planta
            
        Returns:
            Planta con sistemas o None
        """
        query = select(Planta).where(Planta.id == id)
        query = query.options(joinedload(Planta.sistemas))
        return session.exec(query).first()
    
    def get_by_contrato(self, session: Session, contrato_id: int) -> List[Planta]:
        """
        Lista todas las plantas de un contrato específico
        
        Args:
            session: Sesión de base de datos
            contrato_id: ID del contrato
            
        Returns:
            Lista de plantas del contrato
        """
        query = select(Planta).where(Planta.contrato_id == contrato_id)
        return session.exec(query).all()
    
    def get_jerarquia_completa(self, session: Session, id: int) -> Optional[PlantaJerarquica]:
        """
        Obtiene la jerarquía completa de una planta con sus sistemas, subsistemas y equipos
        
        Args:
            session: Sesión de base de datos
            id: ID de la planta
            
        Returns:
            Estructura jerárquica completa de la planta o None
        """
        planta = session.get(Planta, id)
        if not planta:
            return None
        
        # Construir la jerarquía manualmente para mayor control
        planta_jer = PlantaJerarquica(
            id=planta.id,
            nombre=planta.nombre,
            municipio=planta.municipio,
            localizacion=planta.localizacion,
            sistemas=[]
        )
        
        # Cargar los sistemas
        sistemas = session.exec(
            select(Sistema).where(Sistema.planta_id == id)
        ).all()
        
        for sistema in sistemas:
            sistema_read = SistemaRead(
                id=sistema.id,
                codigo=sistema.codigo,
                nombre=sistema.nombre,
                descripcion=sistema.descripcion or "",
                subsistemas=[]
            )
            
            # Cargar los subsistemas de este sistema
            subsistemas = session.exec(
                select(SubSistema).where(SubSistema.sistema_id == sistema.id)
            ).all()
            
            for subsistema in subsistemas:
                subsistema_read = SubSistemaRead(
                    id=subsistema.id,
                    codigo=subsistema.codigo,
                    nombre=subsistema.nombre,
                    descripcion=subsistema.descripcion or "",
                    equipos=[]
                )
                
                # Cargar los equipos de este subsistema
                equipos = session.exec(
                    select(Equipo).where(Equipo.subsistema_id == subsistema.id)
                ).all()
                
                for equipo in equipos:
                    subsistema_read.equipos.append({
                        "id": equipo.id,
                        "nombre": equipo.nombre
                    })
                
                sistema_read.subsistemas.append(subsistema_read)
            
            planta_jer.sistemas.append(sistema_read)
        
        return planta_jer
    
    def get_all_jerarquias(self, session: Session) -> List[PlantaJerarquica]:
        """
        Obtiene la jerarquía completa de todas las plantas
        
        Args:
            session: Sesión de base de datos
            
        Returns:
            Lista de estructuras jerárquicas completas
        """
        plantas = session.exec(select(Planta)).all()
        resultado = []
        
        for planta in plantas:
            jerarquia = self.get_jerarquia_completa(session, planta.id)
            if jerarquia:
                resultado.append(jerarquia)
        
        return resultado

# CRUD para Sistema
class CRUDSistema(CRUDBase[Sistema, Sistema, Sistema, Sistema]):
    """Operaciones CRUD específicas para el modelo Sistema"""
    
    def get_with_subsistemas(self, session: Session, id: int) -> Optional[Sistema]:
        """
        Obtiene un sistema con sus subsistemas cargados
        
        Args:
            session: Sesión de base de datos
            id: ID del sistema
            
        Returns:
            Sistema con subsistemas o None
        """
        query = select(Sistema).where(Sistema.id == id)
        query = query.options(joinedload(Sistema.subsistemas))
        return session.exec(query).first()
    
    def get_by_planta(self, session: Session, planta_id: int) -> List[Sistema]:
        """
        Lista todos los sistemas de una planta específica
        
        Args:
            session: Sesión de base de datos
            planta_id: ID de la planta
            
        Returns:
            Lista de sistemas de la planta
        """
        query = select(Sistema).where(Sistema.planta_id == planta_id)
        return session.exec(query).all()

# CRUD para SubSistema
class CRUDSubSistema(CRUDBase[SubSistema, SubSistema, SubSistema, SubSistema]):
    """Operaciones CRUD específicas para el modelo SubSistema"""
    
    def get_with_equipos(self, session: Session, id: int) -> Optional[SubSistema]:
        """
        Obtiene un subsistema con sus equipos cargados
        
        Args:
            session: Sesión de base de datos
            id: ID del subsistema
            
        Returns:
            Subsistema con equipos o None
        """
        query = select(SubSistema).where(SubSistema.id == id)
        query = query.options(joinedload(SubSistema.equipos))
        return session.exec(query).first()
    
    def get_by_sistema(self, session: Session, sistema_id: int) -> List[SubSistema]:
        """
        Lista todos los subsistemas de un sistema específico
        
        Args:
            session: Sesión de base de datos
            sistema_id: ID del sistema
            
        Returns:
            Lista de subsistemas del sistema
        """
        query = select(SubSistema).where(SubSistema.sistema_id == sistema_id)
        return session.exec(query).all()

# Instancias CRUD para los modelos
crud_planta = CRUDPlanta(Planta)
crud_sistema = CRUDSistema(Sistema)
crud_subsistema = CRUDSubSistema(SubSistema)