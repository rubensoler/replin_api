"""
Operaciones CRUD genéricas para todos los modelos de la aplicación.
Este módulo proporciona funciones reutilizables para Create, Read, Update, Delete
que pueden usarse con cualquier modelo SQLModel.
"""
from typing import Type, TypeVar, Generic, List, Optional, Any, Dict, Union, Callable
from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import SQLModel, Session, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

# Definir un tipo genérico para modelos
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ReadSchemaType = TypeVar("ReadSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ReadSchemaType]):
    """
    Clase base para operaciones CRUD con tipos genéricos:
    - ModelType: Modelo SQLModel usado en la base de datos
    - CreateSchemaType: Esquema Pydantic para creación
    - UpdateSchemaType: Esquema Pydantic para actualización
    - ReadSchemaType: Esquema Pydantic para lectura
    """

    def __init__(self, model: Type[ModelType]):
        """
        Inicializa el objeto CRUD con el modelo específico
        
        Args:
            model: Clase del modelo SQLModel
        """
        self.model = model

    def get(self, session: Session, id: Any, *, options: List[Callable] = None) -> Optional[ModelType]:
        """
        Obtiene un registro por ID con opciones de carga opcional
        
        Args:
            session: Sesión de base de datos
            id: ID del registro a obtener
            options: Lista opcional de opciones de carga (joinedload)
            
        Returns:
            Instancia del modelo o None si no se encuentra
        """
        query = select(self.model).where(self.model.id == id)
        
        if options:
            for option in options:
                query = query.options(option)
                
        return session.exec(query).first()
    
    def get_by_field(self, session: Session, field_name: str, value: Any) -> Optional[ModelType]:
        """
        Obtiene un registro por un campo específico
        
        Args:
            session: Sesión de base de datos
            field_name: Nombre del campo para filtrar
            value: Valor a buscar
            
        Returns:
            Instancia del modelo o None si no se encuentra
        """
        query = select(self.model).where(getattr(self.model, field_name) == value)
        return session.exec(query).first()

    def get_multi(
        self, 
        session: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        options: List[Callable] = None,
        filters: Dict[str, Any] = None
    ) -> List[ModelType]:
        """
        Obtiene múltiples registros con opciones de paginación, filtrado y carga
        
        Args:
            session: Sesión de base de datos
            skip: Cantidad de registros a omitir (para paginación)
            limit: Cantidad máxima de registros a retornar
            options: Lista opcional de opciones de carga (joinedload)
            filters: Diccionario de filtros {field_name: value}
            
        Returns:
            Lista de instancias del modelo
        """
        query = select(self.model)
        
        if filters:
            for field_name, value in filters.items():
                query = query.where(getattr(self.model, field_name) == value)
        
        if options:
            for option in options:
                query = query.options(option)
                
        return session.exec(query.offset(skip).limit(limit)).all()

    def create(self, session: Session, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Crea un nuevo registro
        
        Args:
            session: Sesión de base de datos
            obj_in: Datos para crear el objeto (esquema o diccionario)
            
        Returns:
            Instancia creada del modelo
        
        Raises:
            HTTPException: Si ocurre un error de integridad
        """
        try:
            if isinstance(obj_in, dict):
                obj_data = obj_in
            else:
                obj_data = obj_in.dict(exclude_unset=True)
                
            db_obj = self.model(**obj_data)  # type: ignore
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            session.rollback()
            error_msg = str(e.orig)
            if "UNIQUE constraint failed" in error_msg:
                field = error_msg.split(":")[-1].strip() if ":" in error_msg else "un campo"
                raise HTTPException(status_code=409, detail=f"Ya existe un registro con el mismo valor en {field}")
            raise HTTPException(status_code=400, detail=f"Error de integridad: {error_msg}")

    def update(
        self,
        session: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Actualiza un registro existente
        
        Args:
            session: Sesión de base de datos
            db_obj: Instancia existente del modelo a actualizar
            obj_in: Datos para actualizar (esquema o diccionario)
            
        Returns:
            Instancia actualizada del modelo
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
                
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def remove(self, session: Session, *, id: Any) -> ModelType:
        """
        Elimina un registro
        
        Args:
            session: Sesión de base de datos
            id: ID del registro a eliminar
            
        Returns:
            La instancia eliminada
            
        Raises:
            HTTPException: Si el registro no existe
        """
        obj = session.get(self.model, id)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} con id {id} no encontrado")
        
        session.delete(obj)
        session.commit()
        return obj
    
    def exists(self, session: Session, id: Any) -> bool:
        """
        Verifica si existe un registro con el ID dado
        
        Args:
            session: Sesión de base de datos
            id: ID a verificar
            
        Returns:
            True si existe, False si no
        """
        obj = session.get(self.model, id)
        return obj is not None


# Ejemplo de uso:
# crud_equipo = CRUDBase[Equipo, EquipoCreate, EquipoUpdate, EquipoRead](Equipo)