"""
Router para cargos, personas y actividades,
utilizando las clases CRUD específicas.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from typing import List, Optional
from datetime import date
from io import BytesIO
import pandas as pd
import os
import shutil

from models.operations import (
    Cargo, Persona, Actividad,
    ActividadCreate, ActividadUpdate, ActividadRead, ActividadDetallada
)
from db import get_session, crud_cargo, crud_persona, crud_actividad
from db import crud_equipo  # Para verificar referencias

# Crear router
router = APIRouter(prefix="/api", tags=["Operaciones"])

# ----------------- ENDPOINTS CARGO -----------------
@router.post("/cargos/", response_model=Cargo)
def crear_cargo(cargo: Cargo, session: Session = Depends(get_session)):
    """Crea un nuevo cargo"""
    return crud_cargo.create(session, obj_in=cargo)

@router.get("/cargos/", response_model=List[Cargo])
def listar_cargos(
    skip: int = 0, 
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Lista todos los cargos"""
    return crud_cargo.get_multi(session, skip=skip, limit=limit)

@router.get("/cargos/{cargo_id}", response_model=Cargo)
def obtener_cargo(cargo_id: int, session: Session = Depends(get_session)):
    """Obtiene un cargo por ID"""
    cargo = crud_cargo.get(session, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo no encontrado")
    return cargo

@router.get("/cargos/{cargo_id}/personas", response_model=List[Persona])
def obtener_personas_por_cargo(cargo_id: int, session: Session = Depends(get_session)):
    """Obtiene todas las personas con un cargo específico"""
    # Verificar que existe el cargo
    if not crud_cargo.exists(session, cargo_id):
        raise HTTPException(status_code=404, detail="Cargo no encontrado")
    
    return crud_persona.get_by_cargo(session, cargo_id)

@router.put("/cargos/{cargo_id}", response_model=Cargo)
def actualizar_cargo(cargo_id: int, cargo_data: Cargo, session: Session = Depends(get_session)):
    """Actualiza un cargo existente"""
    cargo = crud_cargo.get(session, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo no encontrado")
    
    return crud_cargo.update(session, db_obj=cargo, obj_in=cargo_data)

@router.delete("/cargos/{cargo_id}")
def eliminar_cargo(cargo_id: int, session: Session = Depends(get_session)):
    """Elimina un cargo"""
    try:
        crud_cargo.remove(session, id=cargo_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar cargo: {str(e)}")

# ----------------- ENDPOINTS PERSONA -----------------
@router.post("/personas/", response_model=Persona)
def crear_persona(persona: Persona, session: Session = Depends(get_session)):
    """Crea una nueva persona"""
    # Verificar que existe el cargo si se proporciona
    if persona.cargo_id and not crud_cargo.exists(session, persona.cargo_id):
        raise HTTPException(status_code=404, detail="Cargo no encontrado")
    
    return crud_persona.create(session, obj_in=persona)

@router.get("/personas/", response_model=List[Persona])
def listar_personas(
    skip: int = 0, 
    limit: int = 100,
    cargo_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Lista personas con filtros opcionales"""
    filters = {}
    if cargo_id:
        filters["cargo_id"] = cargo_id
        
    return crud_persona.get_multi(session, skip=skip, limit=limit, filters=filters)

@router.get("/personas/{persona_id}", response_model=Persona)
def obtener_persona(persona_id: int, session: Session = Depends(get_session)):
    """Obtiene una persona por ID"""
    persona = crud_persona.get(session, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return persona

@router.put("/personas/{persona_id}", response_model=Persona)
def actualizar_persona(persona_id: int, persona_data: Persona, session: Session = Depends(get_session)):
    """Actualiza una persona existente"""
    persona = crud_persona.get(session, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    
    # Verificar cargo si se va a actualizar
    if persona_data.cargo_id and not crud_cargo.exists(session, persona_data.cargo_id):
        raise HTTPException(status_code=404, detail="Cargo no encontrado")
    
    return crud_persona.update(session, db_obj=persona, obj_in=persona_data)

@router.delete("/personas/{persona_id}")
def eliminar_persona(persona_id: int, session: Session = Depends(get_session)):
    """Elimina una persona"""
    try:
        crud_persona.remove(session, id=persona_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar persona: {str(e)}")

@router.get("/verificar_cv/{persona_id}")
def verificar_cv(persona_id: int):
    """Verifica si existe un CV para una persona"""
    filename = f"assets/cvs/{persona_id}-101.pdf"
    existe = os.path.isfile(filename)
    return {"exists": existe}

@router.post("/upload_cv/{persona_id}")
def upload_cv(persona_id: int, file: UploadFile = File(...)):
    """Sube un CV para una persona"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    filename = f"assets/cvs/{persona_id}-101.pdf"
    os.makedirs("assets/cvs", exist_ok=True)

    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": "Archivo cargado con éxito"}

# ----------------- ENDPOINTS ACTIVIDAD -----------------
@router.post("/actividades/", response_model=ActividadRead)
def crear_actividad(actividad: ActividadCreate, session: Session = Depends(get_session)):
    """Crea una nueva actividad"""
    # Verificar que existen el equipo y la persona
    if not crud_equipo.exists(session, actividad.equipo_id):
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    if not crud_persona.exists(session, actividad.persona_id):
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    
    return crud_actividad.create(session, obj_in=actividad)

@router.get("/actividades/", response_model=List[ActividadRead])
def listar_actividades(
    skip: int = 0, 
    limit: int = 100,
    equipo_id: Optional[int] = None,
    persona_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Lista actividades con filtros opcionales"""
    filters = {}
    if equipo_id:
        filters["equipo_id"] = equipo_id
    if persona_id:
        filters["persona_id"] = persona_id
        
    return crud_actividad.get_multi(session, skip=skip, limit=limit, filters=filters)

@router.get("/actividades/detalladas/", response_model=List[ActividadDetallada])
def listar_actividades_detalladas(
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    persona_id: Optional[int] = Query(None),
    equipo_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Lista actividades con detalles adicionales y filtros"""
    return crud_actividad.get_detalladas(
        session,
        desde=desde,
        hasta=hasta,
        persona_id=persona_id,
        equipo_id=equipo_id
    )

@router.get("/actividades/{actividad_id}", response_model=ActividadRead)
def obtener_actividad(actividad_id: int, session: Session = Depends(get_session)):
    """Obtiene una actividad por ID"""
    actividad = crud_actividad.get(session, actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return actividad

@router.put("/actividades/{actividad_id}", response_model=ActividadRead)
def actualizar_actividad(actividad_id: int, actividad_data: ActividadUpdate, session: Session = Depends(get_session)):
    """Actualiza una actividad existente"""
    actividad = crud_actividad.get(session, actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    # Verificar equipo y persona si se van a actualizar
    if actividad_data.equipo_id is not None and not crud_equipo.exists(session, actividad_data.equipo_id):
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    if actividad_data.persona_id is not None and not crud_persona.exists(session, actividad_data.persona_id):
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    
    return crud_actividad.update(session, db_obj=actividad, obj_in=actividad_data)

@router.delete("/actividades/{actividad_id}")
def eliminar_actividad(actividad_id: int, session: Session = Depends(get_session)):
    """Elimina una actividad"""
    try:
        crud_actividad.remove(session, id=actividad_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar actividad: {str(e)}")

@router.get("/actividades/exportar/")
def exportar_actividades_detalladas(
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    persona_id: Optional[int] = Query(None),
    equipo_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Exporta actividades a Excel con filtros opcionales"""
    actividades_detalladas = crud_actividad.get_detalladas(
        session,
        desde=desde,
        hasta=hasta,
        persona_id=persona_id,
        equipo_id=equipo_id
    )
    
    # Convertir a formato para Excel
    data = []
    for act in actividades_detalladas:
        data.append({
            "Fecha": act.fecha.strftime("%Y-%m-%d"),
            "Descripción": act.descripcion,
            "Persona": act.persona,
            "Cargo": act.cargo or "",
            "Equipo": act.equipo
        })
    
    # Crear Excel en memoria
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Actividades')
    output.seek(0)
    
    # Devolver como archivo descargable
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": "attachment; filename=actividades.xlsx"}
    )