"""
Router para clientes, contratos y relaciones de negocio,
utilizando las clases CRUD específicas.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from models.business import (
    Cliente, Contrato, ContratoUsuario
)
from db import get_session, crud_cliente, crud_contrato, crud_contrato_usuario
from db import crud_usuario  # Para verificar referencias

# Crear router
router = APIRouter(prefix="/api", tags=["Negocio"])

# ----------------- ENDPOINTS CLIENTE -----------------
@router.post("/clientes/", response_model=Cliente)
def crear_cliente(cliente: Cliente, session: Session = Depends(get_session)):
    """Crea un nuevo cliente"""
    return crud_cliente.create(session, obj_in=cliente)

@router.get("/clientes/", response_model=List[Cliente])
def listar_clientes(
    skip: int = 0, 
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Lista todos los clientes"""
    return crud_cliente.get_multi(session, skip=skip, limit=limit)

@router.get("/clientes/with-contratos", response_model=List[Cliente])
def listar_clientes_con_contratos(session: Session = Depends(get_session)):
    """Lista todos los clientes con sus contratos"""
    return crud_cliente.get_all_with_contratos(session)

@router.get("/clientes/{cliente_id}", response_model=Cliente)
def obtener_cliente(cliente_id: int, session: Session = Depends(get_session)):
    """Obtiene un cliente por ID"""
    cliente = crud_cliente.get(session, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.get("/clientes/{cliente_id}/with-contratos", response_model=Cliente)
def obtener_cliente_con_contratos(cliente_id: int, session: Session = Depends(get_session)):
    """Obtiene un cliente por ID con sus contratos"""
    cliente = crud_cliente.get_with_contratos(session, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.get("/clientes/{cliente_id}/contratos", response_model=List[Contrato])
def obtener_contratos_cliente(cliente_id: int, session: Session = Depends(get_session)):
    """Obtiene todos los contratos de un cliente"""
    # Verificar que existe el cliente
    if not crud_cliente.exists(session, cliente_id):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return crud_contrato.get_by_cliente(session, cliente_id)

@router.put("/clientes/{cliente_id}", response_model=Cliente)
def actualizar_cliente(cliente_id: int, cliente_data: Cliente, session: Session = Depends(get_session)):
    """Actualiza un cliente existente"""
    cliente = crud_cliente.get(session, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return crud_cliente.update(session, db_obj=cliente, obj_in=cliente_data)

@router.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, session: Session = Depends(get_session)):
    """Elimina un cliente"""
    try:
        crud_cliente.remove(session, id=cliente_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {str(e)}")

# ----------------- ENDPOINTS CONTRATO -----------------
@router.post("/contratos/", response_model=Contrato)
def crear_contrato(contrato: Contrato, session: Session = Depends(get_session)):
    """Crea un nuevo contrato"""
    # Verificar que existe el cliente
    if not crud_cliente.exists(session, contrato.cliente_id):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return crud_contrato.create(session, obj_in=contrato)

@router.get("/contratos/", response_model=List[Contrato])
def listar_contratos(
    skip: int = 0, 
    limit: int = 100,
    cliente_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Lista contratos con filtros opcionales"""
    filters = {}
    if cliente_id:
        filters["cliente_id"] = cliente_id
        
    return crud_contrato.get_multi(session, skip=skip, limit=limit, filters=filters)

@router.get("/contratos/by-usuario/{usuario_id}", response_model=List[Contrato])
def listar_contratos_por_usuario(usuario_id: int, session: Session = Depends(get_session)):
    """Lista todos los contratos asignados a un usuario"""
    # Verificar que existe el usuario
    if not crud_usuario.exists(session, usuario_id):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return crud_contrato.get_by_usuario(session, usuario_id)

@router.get("/contratos/{contrato_id}", response_model=Contrato)
def obtener_contrato(contrato_id: int, session: Session = Depends(get_session)):
    """Obtiene un contrato por ID"""
    contrato = crud_contrato.get(session, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return contrato

@router.get("/contratos/{contrato_id}/with-plantas", response_model=Contrato)
def obtener_contrato_con_plantas(contrato_id: int, session: Session = Depends(get_session)):
    """Obtiene un contrato por ID con sus plantas"""
    contrato = crud_contrato.get_with_plantas(session, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return contrato

@router.put("/contratos/{contrato_id}", response_model=Contrato)
def actualizar_contrato(contrato_id: int, contrato_data: Contrato, session: Session = Depends(get_session)):
    """Actualiza un contrato existente"""
    contrato = crud_contrato.get(session, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    # Verificar cliente si se va a actualizar
    if contrato_data.cliente_id and not crud_cliente.exists(session, contrato_data.cliente_id):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return crud_contrato.update(session, db_obj=contrato, obj_in=contrato_data)

@router.delete("/contratos/{contrato_id}")
def eliminar_contrato(contrato_id: int, session: Session = Depends(get_session)):
    """Elimina un contrato"""
    try:
        crud_contrato.remove(session, id=contrato_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar contrato: {str(e)}")

@router.post("/clientes/{cliente_id}/contratos/{contrato_id}", response_model=Contrato)
def asignar_contrato_a_cliente(cliente_id: int, contrato_id: int, session: Session = Depends(get_session)):
    """Asigna un contrato a un cliente"""
    cliente = crud_cliente.get(session, cliente_id)
    contrato = crud_contrato.get(session, contrato_id)
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    contrato.cliente_id = cliente_id
    session.add(contrato)
    session.commit()
    session.refresh(contrato)
    return contrato

@router.delete("/clientes/{cliente_id}/contratos/{contrato_id}")
def eliminar_contrato_cliente(cliente_id: int, contrato_id: int, session: Session = Depends(get_session)):
    """Desasocia un contrato de un cliente (sin eliminarlo)"""
    contrato = crud_contrato.get(session, contrato_id)
    
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if contrato.cliente_id != cliente_id:
        raise HTTPException(status_code=400, detail="Este contrato no está asociado con el cliente especificado")
    
    contrato.cliente_id = None  # Desasociar el contrato del cliente
    session.add(contrato)
    session.commit()
    return {"ok": True}

# ----------------- ENDPOINTS ASIGNACIÓN CONTRATO-USUARIO -----------------
@router.post("/usuarios/{usuario_id}/contratos/{contrato_id}")
def asignar_contrato_a_usuario(usuario_id: int, contrato_id: int, session: Session = Depends(get_session)):
    """Asigna un contrato a un usuario"""
    try:
        contrato_usuario = crud_contrato.asignar_a_usuario(session, contrato_id, usuario_id)
        return {"message": "Contrato asignado al usuario"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al asignar contrato: {str(e)}")

@router.delete("/usuarios/{usuario_id}/contratos/{contrato_id}")
def desasignar_contrato_de_usuario(usuario_id: int, contrato_id: int, session: Session = Depends(get_session)):
    """Desasigna un contrato de un usuario"""
    try:
        eliminado = crud_contrato.desasignar_de_usuario(session, contrato_id, usuario_id)
        if eliminado:
            return {"message": "Contrato desasignado del usuario"}
        else:
            raise HTTPException(status_code=404, detail="No se encontró la asignación")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desasignar contrato: {str(e)}")

@router.get("/contratos/{contrato_id}/usuarios")
def obtener_usuarios_contrato(contrato_id: int, session: Session = Depends(get_session)):
    """Obtiene todos los usuarios asignados a un contrato"""
    # Verificar que existe el contrato
    if not crud_contrato.exists(session, contrato_id):
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    # Obtener las asignaciones
    contratos_usuario = crud_contrato_usuario.get_by_contrato(session, contrato_id)
    
    # Obtener los detalles de los usuarios
    usuarios = []
    for cu in contratos_usuario:
        usuario = crud_usuario.get(session, cu.usuario_id)
        if usuario:
            usuarios.append(usuario)
    
    return usuarios