"""
Router para plantas, sistemas y subsistemas, 
utilizando las clases CRUD específicas.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from models.organization import (
    Planta, Sistema, SubSistema, 
    PlantaJerarquica, SistemaRead, SubSistemaRead
)
from db import get_session, crud_planta, crud_sistema, crud_subsistema
from db import crud_contrato  # Para verificar referencias

# Crear router
router = APIRouter(prefix="/api", tags=["Organización"])

# ----------------- ENDPOINTS PLANTA -----------------
@router.post("/plantas/", response_model=Planta)
def crear_planta(planta: Planta, session: Session = Depends(get_session)):
    """Crea una nueva planta"""
    # Verificar que existe el contrato
    if not crud_contrato.exists(session, planta.contrato_id):
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    return crud_planta.create(session, obj_in=planta)

@router.get("/plantas/", response_model=List[Planta])
def listar_plantas(
    skip: int = 0, 
    limit: int = 100,
    contrato_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Lista plantas con filtros opcionales"""
    filters = {}
    if contrato_id:
        filters["contrato_id"] = contrato_id
        
    return crud_planta.get_multi(session, skip=skip, limit=limit, filters=filters)

@router.get("/plantas/{planta_id}", response_model=Planta)
def obtener_planta(planta_id: int, session: Session = Depends(get_session)):
    """Obtiene una planta por ID"""
    planta = crud_planta.get(session, planta_id)
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    return planta

@router.get("/plantas/{planta_id}/sistemas", response_model=List[Sistema])
def obtener_sistemas_planta(planta_id: int, session: Session = Depends(get_session)):
    """Obtiene todos los sistemas de una planta"""
    # Verificar que existe la planta
    if not crud_planta.exists(session, planta_id):
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    
    return crud_sistema.get_by_planta(session, planta_id)

@router.put("/plantas/{planta_id}", response_model=Planta)
def actualizar_planta(planta_id: int, planta_data: Planta, session: Session = Depends(get_session)):
    """Actualiza una planta existente"""
    planta = crud_planta.get(session, planta_id)
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    
    # Verificar contrato si se va a actualizar
    if planta_data.contrato_id and not crud_contrato.exists(session, planta_data.contrato_id):
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    return crud_planta.update(session, db_obj=planta, obj_in=planta_data)

@router.delete("/plantas/{planta_id}")
def eliminar_planta(planta_id: int, session: Session = Depends(get_session)):
    """Elimina una planta"""
    try:
        crud_planta.remove(session, id=planta_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar planta: {str(e)}")

# ----------------- ENDPOINTS SISTEMA -----------------
@router.post("/sistemas/", response_model=Sistema)
def crear_sistema(sistema: Sistema, session: Session = Depends(get_session)):
    """Crea un nuevo sistema"""
    # Verificar que existe la planta
    if not crud_planta.exists(session, sistema.planta_id):
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    
    return crud_sistema.create(session, obj_in=sistema)

@router.get("/sistemas/", response_model=List[Sistema])
def listar_sistemas(
    skip: int = 0, 
    limit: int = 100,
    planta_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Lista sistemas con filtros opcionales"""
    filters = {}
    if planta_id:
        filters["planta_id"] = planta_id
        
    return crud_sistema.get_multi(session, skip=skip, limit=limit, filters=filters)

@router.get("/sistemas/{sistema_id}", response_model=Sistema)
def obtener_sistema(sistema_id: int, session: Session = Depends(get_session)):
    """Obtiene un sistema por ID"""
    sistema = crud_sistema.get(session, sistema_id)
    if not sistema:
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    return sistema

@router.get("/sistemas/{sistema_id}/subsistemas", response_model=List[SubSistema])
def obtener_subsistemas_sistema(sistema_id: int, session: Session = Depends(get_session)):
    """Obtiene todos los subsistemas de un sistema"""
    # Verificar que existe el sistema
    if not crud_sistema.exists(session, sistema_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    
    return crud_subsistema.get_by_sistema(session, sistema_id)

@router.put("/sistemas/{sistema_id}", response_model=Sistema)
def actualizar_sistema(sistema_id: int, sistema_data: Sistema, session: Session = Depends(get_session)):
    """Actualiza un sistema existente"""
    sistema = crud_sistema.get(session, sistema_id)
    if not sistema:
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    
    # Verificar planta si se va a actualizar
    if sistema_data.planta_id and not crud_planta.exists(session, sistema_data.planta_id):
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    
    return crud_sistema.update(session, db_obj=sistema, obj_in=sistema_data)

@router.delete("/sistemas/{sistema_id}")
def eliminar_sistema(sistema_id: int, session: Session = Depends(get_session)):
    """Elimina un sistema"""
    try:
        crud_sistema.remove(session, id=sistema_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar sistema: {str(e)}")

# ----------------- ENDPOINTS SUBSISTEMA -----------------
@router.post("/subsistemas/", response_model=SubSistema)
def crear_subsistema(subsistema: SubSistema, session: Session = Depends(get_session)):
    """Crea un nuevo subsistema"""
    # Verificar que existe el sistema
    if not crud_sistema.exists(session, subsistema.sistema_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    
    return crud_subsistema.create(session, obj_in=subsistema)

@router.get("/subsistemas/", response_model=List[SubSistema])
def listar_subsistemas(
    skip: int = 0, 
    limit: int = 100,
    sistema_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Lista subsistemas con filtros opcionales"""
    filters = {}
    if sistema_id:
        filters["sistema_id"] = sistema_id
        
    return crud_subsistema.get_multi(session, skip=skip, limit=limit, filters=filters)

@router.get("/subsistemas/{subsistema_id}", response_model=SubSistema)
def obtener_subsistema(subsistema_id: int, session: Session = Depends(get_session)):
    """Obtiene un subsistema por ID"""
    subsistema = crud_subsistema.get(session, subsistema_id)
    if not subsistema:
        raise HTTPException(status_code=404, detail="Subsistema no encontrado")
    return subsistema

@router.get("/subsistemas/{subsistema_id}/equipos")
def obtener_equipos_subsistema(subsistema_id: int, session: Session = Depends(get_session)):
    """Obtiene todos los equipos de un subsistema"""
    # Verificar que existe el subsistema
    subsistema = crud_subsistema.get_with_equipos(session, subsistema_id)
    if not subsistema:
        raise HTTPException(status_code=404, detail="Subsistema no encontrado")
    
    return subsistema.equipos

@router.put("/subsistemas/{subsistema_id}", response_model=SubSistema)
def actualizar_subsistema(subsistema_id: int, subsistema_data: SubSistema, session: Session = Depends(get_session)):
    """Actualiza un subsistema existente"""
    subsistema = crud_subsistema.get(session, subsistema_id)
    if not subsistema:
        raise HTTPException(status_code=404, detail="Subsistema no encontrado")
    
    # Verificar sistema si se va a actualizar
    if subsistema_data.sistema_id and not crud_sistema.exists(session, subsistema_data.sistema_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    
    return crud_subsistema.update(session, db_obj=subsistema, obj_in=subsistema_data)

@router.delete("/subsistemas/{subsistema_id}")
def eliminar_subsistema(subsistema_id: int, session: Session = Depends(get_session)):
    """Elimina un subsistema"""
    try:
        crud_subsistema.remove(session, id=subsistema_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar subsistema: {str(e)}")

# ----------------- ENDPOINTS JERARQUÍA -----------------
@router.get("/plantas_jerarquia/", response_model=List[PlantaJerarquica])
def obtener_jerarquia_completa(session: Session = Depends(get_session)):
    """Obtiene la estructura jerárquica completa de todas las plantas"""
    return crud_planta.get_all_jerarquias(session)

@router.get("/plantas/{planta_id}/jerarquia", response_model=PlantaJerarquica)
def obtener_jerarquia_planta(planta_id: int, session: Session = Depends(get_session)):
    """Obtiene la estructura jerárquica completa de una planta"""
    jerarquia = crud_planta.get_jerarquia_completa(session, planta_id)
    if not jerarquia:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    return jerarquia