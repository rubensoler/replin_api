"""
Router para equipos, tipos de activos, fabricantes y modelos, 
utilizando las clases CRUD específicas.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from models.equipment import (
    EquipoCreate, EquipoUpdate, EquipoRead, EquipoReadDetallado,
    TipoActivoCreate, TipoActivoRead, TipoActivoUpdate,
    FabricanteCreate, FabricanteRead, FabricanteUpdate,
    ModeloCreate, ModeloRead, ModeloReadDetallado, ModeloUpdate
)
from db import get_session, crud_equipo, crud_tipo_activo, crud_fabricante, crud_modelo

# Crear router
router = APIRouter(prefix="/api", tags=["Equipos"])

# ----------------- ENDPOINTS EQUIPO -----------------
@router.post("/equipos/", response_model=EquipoRead)
def crear_equipo(equipo: EquipoCreate, session: Session = Depends(get_session)):
    """Crea un nuevo equipo con validaciones"""
    return crud_equipo.create_with_validations(session, obj_in=equipo)

@router.get("/equipos/", response_model=List[EquipoReadDetallado])
def listar_equipos(
    skip: int = 0, 
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Lista equipos con paginación"""
    equipos = crud_equipo.get_multi(
        session, 
        skip=skip, 
        limit=limit,
        options=[
            lambda: crud_equipo.model.subsistema, 
            lambda: crud_equipo.model.tipo_activo,
            lambda: crud_equipo.model.fabricante,
            lambda: crud_equipo.model.modelo
        ]
    )
    return equipos

@router.get("/equipos/{equipo_id}", response_model=EquipoReadDetallado)
def obtener_equipo(equipo_id: int, session: Session = Depends(get_session)):
    """Obtiene un equipo por ID con todos sus detalles"""
    equipo = crud_equipo.get_detallado(session, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return equipo

@router.get("/equipos/filtrar/", response_model=List[EquipoRead])
def filtrar_equipos(
    subsistema_id: Optional[int] = None,
    fabricante_id: Optional[int] = None,
    modelo_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Filtra equipos por subsistema, fabricante y/o modelo"""
    filters = {}
    if subsistema_id is not None:
        filters["subsistema_id"] = subsistema_id
    if fabricante_id is not None:
        filters["fabricante_id"] = fabricante_id
    if modelo_id is not None:
        filters["modelo_id"] = modelo_id
        
    return crud_equipo.get_multi(session, filters=filters)

@router.put("/equipos/{equipo_id}", response_model=EquipoRead)
def actualizar_equipo(equipo_id: int, equipo_data: EquipoUpdate, session: Session = Depends(get_session)):
    """Actualiza un equipo existente"""
    db_equipo = crud_equipo.get(session, equipo_id)
    if not db_equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    # Validaciones adicionales
    if equipo_data.subsistema_id is not None and not crud_equipo.exists(session, equipo_data.subsistema_id):
        raise HTTPException(status_code=404, detail="Subsistema no encontrado")
        
    if equipo_data.tipo_activo_id is not None and not crud_tipo_activo.exists(session, equipo_data.tipo_activo_id):
        raise HTTPException(status_code=404, detail="Tipo de activo no encontrado")
        
    if equipo_data.fabricante_id is not None and not crud_fabricante.exists(session, equipo_data.fabricante_id):
        raise HTTPException(status_code=404, detail="Fabricante no encontrado")
        
    if equipo_data.modelo_id is not None:
        modelo = crud_modelo.get(session, equipo_data.modelo_id)
        if not modelo:
            raise HTTPException(status_code=404, detail="Modelo no encontrado")
            
        # Si se actualiza modelo y fabricante, verificar que coincidan
        fabricante_id = equipo_data.fabricante_id if equipo_data.fabricante_id is not None else db_equipo.fabricante_id
        if fabricante_id and modelo.fabricante_id != fabricante_id:
            raise HTTPException(status_code=400, detail="El modelo no pertenece al fabricante especificado")
    
    return crud_equipo.update(session, db_obj=db_equipo, obj_in=equipo_data)

@router.delete("/equipos/{equipo_id}")
def eliminar_equipo(equipo_id: int, session: Session = Depends(get_session)):
    """Elimina un equipo"""
    try:
        crud_equipo.remove(session, id=equipo_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

# ----------------- ENDPOINTS TIPO DE ACTIVO -----------------
@router.post("/tipos-activo/", response_model=TipoActivoRead)
def crear_tipo_activo(tipo: TipoActivoCreate, session: Session = Depends(get_session)):
    """Crea un nuevo tipo de activo"""
    return crud_tipo_activo.create(session, obj_in=tipo)

@router.get("/tipos-activo/", response_model=List[TipoActivoRead])
def listar_tipos_activo(
    skip: int = 0, 
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Lista tipos de activo"""
    return crud_tipo_activo.get_multi(session, skip=skip, limit=limit)

@router.get("/tipos-activo/{tipo_id}", response_model=TipoActivoRead)
def obtener_tipo_activo(tipo_id: int, session: Session = Depends(get_session)):
    """Obtiene un tipo de activo por ID"""
    tipo = crud_tipo_activo.get(session, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de activo no encontrado")
    return tipo

@router.put("/tipos-activo/{tipo_id}", response_model=TipoActivoRead)
def actualizar_tipo_activo(tipo_id: int, tipo_data: TipoActivoUpdate, session: Session = Depends(get_session)):
    """Actualiza un tipo de activo"""
    tipo = crud_tipo_activo.get(session, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de activo no encontrado")
    return crud_tipo_activo.update(session, db_obj=tipo, obj_in=tipo_data)

@router.delete("/tipos-activo/{tipo_id}")
def eliminar_tipo_activo(tipo_id: int, session: Session = Depends(get_session)):
    """Elimina un tipo de activo"""
    try:
        crud_tipo_activo.remove(session, id=tipo_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

# ----------------- ENDPOINTS FABRICANTE -----------------
@router.post("/fabricantes/", response_model=FabricanteRead)
def crear_fabricante(fabricante: FabricanteCreate, session: Session = Depends(get_session)):
    """Crea un nuevo fabricante"""
    return crud_fabricante.create(session, obj_in=fabricante)

@router.get("/fabricantes/", response_model=List[FabricanteRead])
def listar_fabricantes(
    skip: int = 0, 
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Lista fabricantes"""
    return crud_fabricante.get_multi(session, skip=skip, limit=limit)

@router.get("/fabricantes/with-modelos/", response_model=List[FabricanteRead])
def listar_fabricantes_con_modelos(session: Session = Depends(get_session)):
    """Lista fabricantes con sus modelos incluidos"""
    return crud_fabricante.get_all_with_modelos(session)

@router.get("/fabricantes/{fabricante_id}", response_model=FabricanteRead)
def obtener_fabricante(fabricante_id: int, session: Session = Depends(get_session)):
    """Obtiene un fabricante por ID"""
    fabricante = crud_fabricante.get(session, fabricante_id)
    if not fabricante:
        raise HTTPException(status_code=404, detail="Fabricante no encontrado")
    return fabricante

@router.get("/fabricantes/{fabricante_id}/modelos", response_model=List[ModeloRead])
def listar_modelos_por_fabricante(fabricante_id: int, session: Session = Depends(get_session)):
    """Lista todos los modelos de un fabricante específico"""
    # Verificar que el fabricante existe
    if not crud_fabricante.exists(session, fabricante_id):
        raise HTTPException(status_code=404, detail="Fabricante no encontrado")
    
    # Usar filtros en get_multi
    return crud_modelo.get_multi(session, filters={"fabricante_id": fabricante_id})

@router.put("/fabricantes/{fabricante_id}", response_model=FabricanteRead)
def actualizar_fabricante(fabricante_id: int, fabricante_data: FabricanteUpdate, session: Session = Depends(get_session)):
    """Actualiza un fabricante"""
    fabricante = crud_fabricante.get(session, fabricante_id)
    if not fabricante:
        raise HTTPException(status_code=404, detail="Fabricante no encontrado")
    return crud_fabricante.update(session, db_obj=fabricante, obj_in=fabricante_data)

@router.delete("/fabricantes/{fabricante_id}")
def eliminar_fabricante(fabricante_id: int, session: Session = Depends(get_session)):
    """Elimina un fabricante"""
    try:
        crud_fabricante.remove(session, id=fabricante_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

# ----------------- ENDPOINTS MODELO -----------------
@router.post("/modelos/", response_model=ModeloRead)
def crear_modelo(modelo: ModeloCreate, session: Session = Depends(get_session)):
    """Crea un nuevo modelo"""
    return crud_modelo.create_with_validation(session, obj_in=modelo)

@router.get("/modelos/", response_model=List[ModeloReadDetallado])
def listar_modelos(
    skip: int = 0, 
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Lista modelos con detalles del fabricante"""
    return crud_modelo.get_all_con_fabricante(session)

@router.get("/modelos/{modelo_id}", response_model=ModeloReadDetallado)
def obtener_modelo(modelo_id: int, session: Session = Depends(get_session)):
    """Obtiene un modelo por ID con detalles del fabricante"""
    modelo = crud_modelo.get_con_fabricante(session, modelo_id)
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    return modelo

@router.put("/modelos/{modelo_id}", response_model=ModeloRead)
def actualizar_modelo(modelo_id: int, modelo_data: ModeloUpdate, session: Session = Depends(get_session)):
    """Actualiza un modelo"""
    modelo = crud_modelo.get(session, modelo_id)
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    
    # Validar fabricante si se actualiza
    if modelo_data.fabricante_id is not None and not crud_fabricante.exists(session, modelo_data.fabricante_id):
        raise HTTPException(status_code=404, detail="Fabricante no encontrado")
    
    return crud_modelo.update(session, db_obj=modelo, obj_in=modelo_data)

@router.delete("/modelos/{modelo_id}")
def eliminar_modelo(modelo_id: int, session: Session = Depends(get_session)):
    """Elimina un modelo"""
    try:
        crud_modelo.remove(session, id=modelo_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")