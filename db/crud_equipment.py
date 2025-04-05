"""
Operaciones CRUD específicas para equipos, tipos de activos, fabricantes y modelos.
"""
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any, Union
from sqlmodel import Session, select

from db.crud import CRUDBase
from models.equipment import (
    Equipo, EquipoCreate, EquipoUpdate, EquipoRead, EquipoReadDetallado,
    TipoActivo, TipoActivoCreate, TipoActivoUpdate, TipoActivoRead,
    Fabricante, FabricanteCreate, FabricanteUpdate, FabricanteRead,
    Modelo, ModeloCreate, ModeloUpdate, ModeloRead, ModeloReadDetallado
)
from models.organization import SubSistema

# CRUD para Equipo con métodos personalizados
class CRUDEquipo(CRUDBase[Equipo, EquipoCreate, EquipoUpdate, EquipoRead]):
    """Operaciones CRUD específicas para el modelo Equipo"""
    
    def get_detallado(self, session: Session, id: int) -> Optional[Equipo]:
        """
        Obtiene un equipo con todas sus relaciones cargadas
        
        Args:
            session: Sesión de base de datos
            id: ID del equipo
            
        Returns:
            Equipo con todas sus relaciones cargadas o None
        """
        query = select(Equipo).where(Equipo.id == id)
        query = query.options(
            joinedload(Equipo.subsistema),
            joinedload(Equipo.tipo_activo),
            joinedload(Equipo.fabricante),
            joinedload(Equipo.modelo)
        )
        return session.exec(query).first()
    
    def get_by_subsistema(self, session: Session, subsistema_id: int) -> List[Equipo]:
        """
        Lista todos los equipos de un subsistema específico
        
        Args:
            session: Sesión de base de datos
            subsistema_id: ID del subsistema
            
        Returns:
            Lista de equipos que pertenecen al subsistema
        """
        query = select(Equipo).where(Equipo.subsistema_id == subsistema_id)
        return session.exec(query).all()
    
    def get_by_fabricante_modelo(
        self, 
        session: Session, 
        fabricante_id: Optional[int] = None,
        modelo_id: Optional[int] = None
    ) -> List[Equipo]:
        """
        Lista equipos filtrados por fabricante y/o modelo
        
        Args:
            session: Sesión de base de datos
            fabricante_id: ID opcional del fabricante
            modelo_id: ID opcional del modelo
            
        Returns:
            Lista de equipos que cumplen con los criterios
        """
        query = select(Equipo)
        
        if fabricante_id is not None:
            query = query.where(Equipo.fabricante_id == fabricante_id)
            
        if modelo_id is not None:
            query = query.where(Equipo.modelo_id == modelo_id)
            
        return session.exec(query).all()
    
    def create_with_validations(
        self, 
        session: Session, 
        *, 
        obj_in: Union[EquipoCreate, Dict[str, Any]]
    ) -> Equipo:
        """
        Crea un equipo con validaciones adicionales
        
        Args:
            session: Sesión de base de datos
            obj_in: Datos para crear el equipo
            
        Returns:
            Equipo creado
            
        Raises:
            HTTPException: Si alguna validación falla
        """
        from fastapi import HTTPException
        
        # Convertir a diccionario si es un modelo Pydantic
        if isinstance(obj_in, EquipoCreate):
            data = obj_in.dict(exclude_unset=True)
        else:
            data = obj_in
            
        # Validar que existe el subsistema
        subsistema_id = data.get("subsistema_id")
        if not session.get(SubSistema, subsistema_id):
            raise HTTPException(status_code=404, detail="Subsistema no encontrado")
        
        # Validar que existe el tipo de activo
        tipo_activo_id = data.get("tipo_activo_id")
        if not session.get(TipoActivo, tipo_activo_id):
            raise HTTPException(status_code=404, detail="Tipo de activo no encontrado")
        
        # Validar fabricante si se proporciona
        fabricante_id = data.get("fabricante_id")
        if fabricante_id and not session.get(Fabricante, fabricante_id):
            raise HTTPException(status_code=404, detail="Fabricante no encontrado")
        
        # Validar modelo si se proporciona
        modelo_id = data.get("modelo_id")
        if modelo_id:
            modelo = session.get(Modelo, modelo_id)
            if not modelo:
                raise HTTPException(status_code=404, detail="Modelo no encontrado")
            
            # Validar que el modelo pertenece al fabricante especificado
            if fabricante_id and modelo.fabricante_id != fabricante_id:
                raise HTTPException(
                    status_code=400, 
                    detail="El modelo no pertenece al fabricante especificado"
                )
        
        # Crear el equipo
        return super().create(session, obj_in=data)

# CRUD para Fabricante
class CRUDFabricante(CRUDBase[Fabricante, FabricanteCreate, FabricanteUpdate, FabricanteRead]):
    """Operaciones CRUD específicas para el modelo Fabricante"""
    
    def get_with_modelos(self, session: Session, id: int) -> Optional[Fabricante]:
        """
        Obtiene un fabricante con sus modelos cargados
        
        Args:
            session: Sesión de base de datos
            id: ID del fabricante
            
        Returns:
            Fabricante con modelos o None
        """
        query = select(Fabricante).where(Fabricante.id == id)
        query = query.options(joinedload(Fabricante.modelos))
        return session.exec(query).first()
    
    def get_all_with_modelos(self, session: Session) -> List[Fabricante]:
        """
        Obtiene todos los fabricantes con sus modelos cargados
        
        Args:
            session: Sesión de base de datos
            
        Returns:
            Lista de fabricantes con sus modelos
        """
        query = select(Fabricante).options(joinedload(Fabricante.modelos))
        return session.exec(query).all()

# CRUD para Modelo
class CRUDModelo(CRUDBase[Modelo, ModeloCreate, ModeloUpdate, ModeloRead]):
    """Operaciones CRUD específicas para el modelo Modelo"""
    
    def get_con_fabricante(self, session: Session, id: int) -> Optional[Modelo]:
        """
        Obtiene un modelo con su fabricante cargado
        
        Args:
            session: Sesión de base de datos
            id: ID del modelo
            
        Returns:
            Modelo con fabricante o None
        """
        query = select(Modelo).where(Modelo.id == id)
        query = query.options(joinedload(Modelo.fabricante))
        return session.exec(query).first()
    
    def get_all_con_fabricante(self, session: Session) -> List[Modelo]:
        """
        Obtiene todos los modelos con su fabricante cargado
        
        Args:
            session: Sesión de base de datos
            
        Returns:
            Lista de modelos con su fabricante
        """
        query = select(Modelo).options(joinedload(Modelo.fabricante))
        return session.exec(query).all()
    
    def create_with_validation(self, session: Session, *, obj_in: ModeloCreate) -> Modelo:
        """
        Crea un modelo con validación del fabricante
        
        Args:
            session: Sesión de base de datos
            obj_in: Datos para crear el modelo
            
        Returns:
            Modelo creado
            
        Raises:
            HTTPException: Si el fabricante no existe
        """
        from fastapi import HTTPException
        
        # Validar que existe el fabricante
        fabricante = session.get(Fabricante, obj_in.fabricante_id)
        if not fabricante:
            raise HTTPException(status_code=404, detail="Fabricante no encontrado")
        
        return super().create(session, obj_in=obj_in)

# Instancias CRUD para los modelos
crud_equipo = CRUDEquipo(Equipo)
crud_tipo_activo = CRUDBase[TipoActivo, TipoActivoCreate, TipoActivoUpdate, TipoActivoRead](TipoActivo)
crud_fabricante = CRUDFabricante(Fabricante)
crud_modelo = CRUDModelo(Modelo)