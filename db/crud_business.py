"""
Operaciones CRUD específicas para clientes, contratos y relaciones de negocio.
"""
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select

from db.crud import CRUDBase
from models.business import (
    Cliente, Contrato, ContratoUsuario
)
from models.users import Usuario

# CRUD para Cliente
class CRUDCliente(CRUDBase[Cliente, Cliente, Cliente, Cliente]):
    """Operaciones CRUD específicas para el modelo Cliente"""
    
    def get_with_contratos(self, session: Session, id: int) -> Optional[Cliente]:
        """
        Obtiene un cliente con sus contratos cargados
        
        Args:
            session: Sesión de base de datos
            id: ID del cliente
            
        Returns:
            Cliente con contratos o None
        """
        query = select(Cliente).where(Cliente.id == id)
        query = query.options(joinedload(Cliente.contratos))
        return session.exec(query).first()
    
    def get_all_with_contratos(self, session: Session) -> List[Cliente]:
        """
        Obtiene todos los clientes con sus contratos cargados
        
        Args:
            session: Sesión de base de datos
            
        Returns:
            Lista de clientes con sus contratos
        """
        query = select(Cliente).options(joinedload(Cliente.contratos))
        return session.exec(query).all()

# CRUD para Contrato
class CRUDContrato(CRUDBase[Contrato, Contrato, Contrato, Contrato]):
    """Operaciones CRUD específicas para el modelo Contrato"""
    
    def get_with_plantas(self, session: Session, id: int) -> Optional[Contrato]:
        """
        Obtiene un contrato con sus plantas cargadas
        
        Args:
            session: Sesión de base de datos
            id: ID del contrato
            
        Returns:
            Contrato con plantas o None
        """
        query = select(Contrato).where(Contrato.id == id)
        query = query.options(joinedload(Contrato.plantas))
        return session.exec(query).first()
    
    def get_by_cliente(self, session: Session, cliente_id: int) -> List[Contrato]:
        """
        Lista todos los contratos de un cliente específico
        
        Args:
            session: Sesión de base de datos
            cliente_id: ID del cliente
            
        Returns:
            Lista de contratos del cliente
        """
        query = select(Contrato).where(Contrato.cliente_id == cliente_id)
        return session.exec(query).all()
    
    def get_by_usuario(self, session: Session, usuario_id: int) -> List[Contrato]:
        """
        Lista todos los contratos asignados a un usuario específico
        
        Args:
            session: Sesión de base de datos
            usuario_id: ID del usuario
            
        Returns:
            Lista de contratos del usuario
        """
        # Obtener los IDs de contratos del usuario a través de la tabla intermedia
        contratos_usuario = session.exec(
            select(ContratoUsuario).where(ContratoUsuario.usuario_id == usuario_id)
        ).all()
        
        contrato_ids = [cu.contrato_id for cu in contratos_usuario]
        
        if not contrato_ids:
            return []
        
        # Obtener los contratos completos
        query = select(Contrato).where(Contrato.id.in_(contrato_ids))
        return session.exec(query).all()
    
    def asignar_a_usuario(self, session: Session, contrato_id: int, usuario_id: int) -> ContratoUsuario:
        """
        Asigna un contrato a un usuario
        
        Args:
            session: Sesión de base de datos
            contrato_id: ID del contrato
            usuario_id: ID del usuario
            
        Returns:
            Relación ContratoUsuario creada
            
        Raises:
            HTTPException: Si el contrato o usuario no existen o si ya existe la relación
        """
        from fastapi import HTTPException
        
        # Verificar que existen el contrato y el usuario
        contrato = session.get(Contrato, contrato_id)
        usuario = session.get(Usuario, usuario_id)
        
        if not contrato:
            raise HTTPException(status_code=404, detail="Contrato no encontrado")
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar si ya existe la relación
        existing = session.exec(
            select(ContratoUsuario).where(
                ContratoUsuario.contrato_id == contrato_id,
                ContratoUsuario.usuario_id == usuario_id
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=409, detail="Este usuario ya tiene asignado este contrato")
        
        # Crear la relación
        contrato_usuario = ContratoUsuario(contrato_id=contrato_id, usuario_id=usuario_id)
        session.add(contrato_usuario)
        session.commit()
        session.refresh(contrato_usuario)
        
        return contrato_usuario
    
    def desasignar_de_usuario(self, session: Session, contrato_id: int, usuario_id: int) -> bool:
        """
        Desasigna un contrato de un usuario
        
        Args:
            session: Sesión de base de datos
            contrato_id: ID del contrato
            usuario_id: ID del usuario
            
        Returns:
            True si se eliminó la relación, False si no existía
            
        Raises:
            HTTPException: Si ocurre un error al eliminar la relación
        """
        from fastapi import HTTPException
        
        # Buscar la relación
        contrato_usuario = session.exec(
            select(ContratoUsuario).where(
                ContratoUsuario.contrato_id == contrato_id,
                ContratoUsuario.usuario_id == usuario_id
            )
        ).first()
        
        if not contrato_usuario:
            return False
        
        try:
            session.delete(contrato_usuario)
            session.commit()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al desasignar contrato: {str(e)}")

# CRUD para ContratoUsuario
class CRUDContratoUsuario(CRUDBase[ContratoUsuario, ContratoUsuario, ContratoUsuario, ContratoUsuario]):
    """Operaciones CRUD específicas para el modelo ContratoUsuario"""
    
    def get_by_contrato(self, session: Session, contrato_id: int) -> List[ContratoUsuario]:
        """
        Lista todas las relaciones de un contrato específico
        
        Args:
            session: Sesión de base de datos
            contrato_id: ID del contrato
            
        Returns:
            Lista de relaciones del contrato
        """
        query = select(ContratoUsuario).where(ContratoUsuario.contrato_id == contrato_id)
        return session.exec(query).all()
    
    def get_by_usuario(self, session: Session, usuario_id: int) -> List[ContratoUsuario]:
        """
        Lista todas las relaciones de un usuario específico
        
        Args:
            session: Sesión de base de datos
            usuario_id: ID del usuario
            
        Returns:
            Lista de relaciones del usuario
        """
        query = select(ContratoUsuario).where(ContratoUsuario.usuario_id == usuario_id)
        return session.exec(query).all()
    
    def get_by_contrato_usuario(self, session: Session, contrato_id: int, usuario_id: int) -> Optional[ContratoUsuario]:
        """
        Obtiene una relación específica entre contrato y usuario
        
        Args:
            session: Sesión de base de datos
            contrato_id: ID del contrato
            usuario_id: ID del usuario
            
        Returns:
            Relación encontrada o None
        """
        query = select(ContratoUsuario).where(
            ContratoUsuario.contrato_id == contrato_id,
            ContratoUsuario.usuario_id == usuario_id
        )
        return session.exec(query).first()

# Instancias CRUD para los modelos
crud_cliente = CRUDCliente(Cliente)
crud_contrato = CRUDContrato(Contrato)
crud_contrato_usuario = CRUDContratoUsuario(ContratoUsuario)