"""
Operaciones CRUD específicas para usuarios, roles y aplicaciones.
"""
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select

from db.crud import CRUDBase
from models.users import (
    Usuario, Rol, Aplicacion, AplicacionRol
)

# CRUD para Usuario
class CRUDUsuario(CRUDBase[Usuario, Usuario, Usuario, Usuario]):
    """Operaciones CRUD específicas para el modelo Usuario"""
    
    def get_with_rol(self, session: Session, id: int) -> Optional[Usuario]:
        """
        Obtiene un usuario con su rol cargado
        
        Args:
            session: Sesión de base de datos
            id: ID del usuario
            
        Returns:
            Usuario con rol o None
        """
        query = select(Usuario).where(Usuario.id == id)
        query = query.options(joinedload(Usuario.rol))
        return session.exec(query).first()
    
    def get_by_username(self, session: Session, username: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su nombre de usuario
        
        Args:
            session: Sesión de base de datos
            username: Nombre de usuario
            
        Returns:
            Usuario encontrado o None
        """
        query = select(Usuario).where(Usuario.username == username)
        return session.exec(query).first()
    
    def get_by_rol(self, session: Session, rol_id: int) -> List[Usuario]:
        """
        Lista todos los usuarios con un rol específico
        
        Args:
            session: Sesión de base de datos
            rol_id: ID del rol
            
        Returns:
            Lista de usuarios con el rol
        """
        query = select(Usuario).where(Usuario.rol_id == rol_id)
        return session.exec(query).all()
    
    def authenticate(self, session: Session, username: str, password: str) -> Optional[Usuario]:
        """
        Autentica un usuario verificando username y password
        
        Args:
            session: Sesión de base de datos
            username: Nombre de usuario
            password: Contraseña en texto plano (debe usarse hash en producción)
            
        Returns:
            Usuario autenticado o None
        """
        query = select(Usuario).where(
            Usuario.username == username,
            Usuario.password == password  # En producción: usar hash
        )
        return session.exec(query).first()

# CRUD para Rol
class CRUDRol(CRUDBase[Rol, Rol, Rol, Rol]):
    """Operaciones CRUD específicas para el modelo Rol"""
    
    def get_with_usuarios(self, session: Session, id: int) -> Optional[Rol]:
        """
        Obtiene un rol con sus usuarios cargados
        
        Args:
            session: Sesión de base de datos
            id: ID del rol
            
        Returns:
            Rol con usuarios o None
        """
        query = select(Rol).where(Rol.id == id)
        query = query.options(joinedload(Rol.usuarios))
        return session.exec(query).first()
    
    def get_with_aplicaciones(self, session: Session, id: int) -> Optional[Rol]:
        """
        Obtiene un rol con sus aplicaciones cargadas
        
        Args:
            session: Sesión de base de datos
            id: ID del rol
            
        Returns:
            Rol con aplicaciones o None
        """
        query = select(Rol).where(Rol.id == id)
        query = query.options(joinedload(Rol.aplicaciones).joinedload(AplicacionRol.aplicacion))
        return session.exec(query).first()

# CRUD para Aplicacion
class CRUDAplicacion(CRUDBase[Aplicacion, Aplicacion, Aplicacion, Aplicacion]):
    """Operaciones CRUD específicas para el modelo Aplicacion"""
    
    def get_with_roles(self, session: Session, id: int) -> Optional[Aplicacion]:
        """
        Obtiene una aplicación con sus roles cargados
        
        Args:
            session: Sesión de base de datos
            id: ID de la aplicación
            
        Returns:
            Aplicación con roles o None
        """
        query = select(Aplicacion).where(Aplicacion.id == id)
        query = query.options(joinedload(Aplicacion.roles).joinedload(AplicacionRol.rol))
        return session.exec(query).first()
    
    def get_by_rol(self, session: Session, rol_id: int) -> List[Aplicacion]:
        """
        Lista todas las aplicaciones asignadas a un rol específico
        
        Args:
            session: Sesión de base de datos
            rol_id: ID del rol
            
        Returns:
            Lista de aplicaciones asignadas al rol
        """
        # Obtener las relaciones AplicacionRol del rol
        aplicaciones_rol = session.exec(
            select(AplicacionRol).where(AplicacionRol.rol_id == rol_id)
        ).all()
        
        aplicacion_ids = [ar.aplicacion_id for ar in aplicaciones_rol]
        
        if not aplicacion_ids:
            return []
        
        # Obtener las aplicaciones completas
        query = select(Aplicacion).where(Aplicacion.id.in_(aplicacion_ids))
        return session.exec(query).all()

# CRUD para AplicacionRol
class CRUDAplicacionRol(CRUDBase[AplicacionRol, AplicacionRol, AplicacionRol, AplicacionRol]):
    """Operaciones CRUD específicas para el modelo AplicacionRol"""
    
    def get_by_rol(self, session: Session, rol_id: int) -> List[AplicacionRol]:
        """
        Lista todas las relaciones de un rol específico
        
        Args:
            session: Sesión de base de datos
            rol_id: ID del rol
            
        Returns:
            Lista de relaciones del rol
        """
        query = select(AplicacionRol).where(AplicacionRol.rol_id == rol_id)
        return session.exec(query).all()
    
    def get_by_aplicacion(self, session: Session, aplicacion_id: int) -> List[AplicacionRol]:
        """
        Lista todas las relaciones de una aplicación específica
        
        Args:
            session: Sesión de base de datos
            aplicacion_id: ID de la aplicación
            
        Returns:
            Lista de relaciones de la aplicación
        """
        query = select(AplicacionRol).where(AplicacionRol.aplicacion_id == aplicacion_id)
        return session.exec(query).all()
    
    def asignar_aplicacion_a_rol(self, session: Session, aplicacion_id: int, rol_id: int) -> AplicacionRol:
        """
        Asigna una aplicación a un rol
        
        Args:
            session: Sesión de base de datos
            aplicacion_id: ID de la aplicación
            rol_id: ID del rol
            
        Returns:
            Relación AplicacionRol creada
            
        Raises:
            HTTPException: Si la aplicación o rol no existen o si ya existe la relación
        """
        from fastapi import HTTPException
        
        # Verificar que existen la aplicación y el rol
        aplicacion = session.get(Aplicacion, aplicacion_id)
        rol = session.get(Rol, rol_id)
        
        if not aplicacion:
            raise HTTPException(status_code=404, detail="Aplicación no encontrada")
        if not rol:
            raise HTTPException(status_code=404, detail="Rol no encontrado")
        
        # Verificar si ya existe la relación
        existing = session.exec(
            select(AplicacionRol).where(
                AplicacionRol.aplicacion_id == aplicacion_id,
                AplicacionRol.rol_id == rol_id
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=409, detail="Esta aplicación ya está asignada a este rol")
        
        # Crear la relación
        aplicacion_rol = AplicacionRol(aplicacion_id=aplicacion_id, rol_id=rol_id)
        session.add(aplicacion_rol)
        session.commit()
        session.refresh(aplicacion_rol)
        
        return aplicacion_rol
    
    def desasignar_aplicacion_de_rol(self, session: Session, aplicacion_id: int, rol_id: int) -> bool:
        """
        Desasigna una aplicación de un rol
        
        Args:
            session: Sesión de base de datos
            aplicacion_id: ID de la aplicación
            rol_id: ID del rol
            
        Returns:
            True si se eliminó la relación, False si no existía
            
        Raises:
            HTTPException: Si ocurre un error al eliminar la relación
        """
        from fastapi import HTTPException
        
        # Buscar la relación
        aplicacion_rol = session.exec(
            select(AplicacionRol).where(
                AplicacionRol.aplicacion_id == aplicacion_id,
                AplicacionRol.rol_id == rol_id
            )
        ).first()
        
        if not aplicacion_rol:
            return False
        
        try:
            session.delete(aplicacion_rol)
            session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al desasignar aplicación: {str(e)}")

# Instancias CRUD para los modelos
crud_usuario = CRUDUsuario(Usuario)
crud_rol = CRUDRol(Rol)
crud_aplicacion = CRUDAplicacion(Aplicacion)
crud_aplicacion_rol = CRUDAplicacionRol(AplicacionRol)