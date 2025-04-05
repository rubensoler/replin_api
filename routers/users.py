"""
Router para usuarios, roles y aplicaciones,
utilizando las clases CRUD específicas.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from models.users import (
    Usuario, Rol, Aplicacion, AplicacionRol
)
from db import get_session, crud_usuario, crud_rol, crud_aplicacion, crud_aplicacion_rol

# Crear router
router = APIRouter(prefix="/api", tags=["Usuarios"])

# ----------------- ENDPOINTS USUARIO -----------------
@router.post("/usuarios/", response_model=Usuario)
def crear_usuario(usuario: Usuario, session: Session = Depends(get_session)):
    """Crea un nuevo usuario"""
    # Verificar que existe el rol
    if not crud_rol.exists(session, usuario.rol_id):
        raise HTTPException(status_code=404, detail="Rol no encontrado")
        
    # Verificar que no exista otro usuario con el mismo username
    if crud_usuario.get_by_username(session, usuario.username):
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese nombre de usuario")
    
    return crud_usuario.create(session, obj_in=usuario)

@router.get("/usuarios/", response_model=List[Usuario])
def listar_usuarios(
    skip: int = 0, 
    limit: int = 100,
    rol_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Lista usuarios con filtros opcionales"""
    filters = {}
    if rol_id:
        filters["rol_id"] = rol_id
        
    return crud_usuario.get_multi(session, skip=skip, limit=limit, filters=filters)

@router.get("/usuarios/{usuario_id}", response_model=Usuario)
def obtener_usuario(usuario_id: int, session: Session = Depends(get_session)):
    """Obtiene un usuario por ID"""
    usuario = crud_usuario.get(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.get("/usuarios/by-username/{username}", response_model=Usuario)
def obtener_usuario_por_username(username: str, session: Session = Depends(get_session)):
    """Obtiene un usuario por nombre de usuario"""
    usuario = crud_usuario.get_by_username(session, username)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.put("/usuarios/{usuario_id}", response_model=Usuario)
def actualizar_usuario(usuario_id: int, usuario_data: Usuario, session: Session = Depends(get_session)):
    """Actualiza un usuario existente"""
    usuario = crud_usuario.get(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar que existe el rol si se va a actualizar
    if usuario_data.rol_id and not crud_rol.exists(session, usuario_data.rol_id):
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Verificar que no exista otro usuario con el mismo username
    if usuario_data.username != usuario.username and crud_usuario.get_by_username(session, usuario_data.username):
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese nombre de usuario")
    
    return crud_usuario.update(session, db_obj=usuario, obj_in=usuario_data)

@router.delete("/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int, session: Session = Depends(get_session)):
    """Elimina un usuario"""
    try:
        crud_usuario.remove(session, id=usuario_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)}")

@router.post("/usuarios/{usuario_id}/rol/{rol_id}")
def asignar_rol_a_usuario(usuario_id: int, rol_id: int, session: Session = Depends(get_session)):
    """Asigna un rol a un usuario"""
    usuario = crud_usuario.get(session, usuario_id)
    rol = crud_rol.get(session, rol_id)
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    usuario.rol_id = rol_id
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return {"message": "Rol asignado al usuario"}

# ----------------- ENDPOINTS ROL -----------------
@router.post("/roles/", response_model=Rol)
def crear_rol(rol: Rol, session: Session = Depends(get_session)):
    """Crea un nuevo rol"""
    return crud_rol.create(session, obj_in=rol)

@router.get("/roles/", response_model=List[Rol])
def listar_roles(
    skip: int = 0, 
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Lista todos los roles"""
    return crud_rol.get_multi(session, skip=skip, limit=limit)

@router.get("/roles/{rol_id}", response_model=Rol)
def obtener_rol(rol_id: int, session: Session = Depends(get_session)):
    """Obtiene un rol por ID"""
    rol = crud_rol.get(session, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol

@router.get("/roles/{rol_id}/with-aplicaciones", response_model=Rol)
def obtener_rol_con_aplicaciones(rol_id: int, session: Session = Depends(get_session)):
    """Obtiene un rol por ID con sus aplicaciones"""
    rol = crud_rol.get_with_aplicaciones(session, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol

@router.get("/roles/{rol_id}/usuarios", response_model=List[Usuario])
def obtener_usuarios_por_rol(rol_id: int, session: Session = Depends(get_session)):
    """Obtiene todos los usuarios con un rol específico"""
    # Verificar que existe el rol
    if not crud_rol.exists(session, rol_id):
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    return crud_usuario.get_by_rol(session, rol_id)

@router.put("/roles/{rol_id}", response_model=Rol)
def actualizar_rol(rol_id: int, rol_data: Rol, session: Session = Depends(get_session)):
    """Actualiza un rol existente"""
    rol = crud_rol.get(session, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    return crud_rol.update(session, db_obj=rol, obj_in=rol_data)

@router.delete("/roles/{rol_id}")
def eliminar_rol(rol_id: int, session: Session = Depends(get_session)):
    """Elimina un rol"""
    try:
        crud_rol.remove(session, id=rol_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar rol: {str(e)}")

# ----------------- ENDPOINTS APLICACION -----------------
@router.post("/aplicaciones/", response_model=Aplicacion)
def crear_aplicacion(aplicacion: Aplicacion, session: Session = Depends(get_session)):
    """Crea una nueva aplicación"""
    return crud_aplicacion.create(session, obj_in=aplicacion)

@router.get("/aplicaciones/", response_model=List[Aplicacion])
def listar_aplicaciones(
    skip: int = 0, 
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Lista todas las aplicaciones"""
    return crud_aplicacion.get_multi(session, skip=skip, limit=limit)

@router.get("/aplicaciones/{aplicacion_id}", response_model=Aplicacion)
def obtener_aplicacion(aplicacion_id: int, session: Session = Depends(get_session)):
    """Obtiene una aplicación por ID"""
    aplicacion = crud_aplicacion.get(session, aplicacion_id)
    if not aplicacion:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    return aplicacion

@router.get("/aplicaciones/by-rol/{rol_id}", response_model=List[Aplicacion])
def listar_aplicaciones_por_rol(rol_id: int, session: Session = Depends(get_session)):
    """Lista todas las aplicaciones asignadas a un rol"""
    # Verificar que existe el rol
    if not crud_rol.exists(session, rol_id):
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    return crud_aplicacion.get_by_rol(session, rol_id)

@router.put("/aplicaciones/{aplicacion_id}", response_model=Aplicacion)
def actualizar_aplicacion(aplicacion_id: int, aplicacion_data: Aplicacion, session: Session = Depends(get_session)):
    """Actualiza una aplicación existente"""
    aplicacion = crud_aplicacion.get(session, aplicacion_id)
    if not aplicacion:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    
    return crud_aplicacion.update(session, db_obj=aplicacion, obj_in=aplicacion_data)

@router.delete("/aplicaciones/{aplicacion_id}")
def eliminar_aplicacion(aplicacion_id: int, session: Session = Depends(get_session)):
    """Elimina una aplicación"""
    try:
        crud_aplicacion.remove(session, id=aplicacion_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar aplicación: {str(e)}")

# ----------------- ENDPOINTS ASIGNACIÓN APLICACION-ROL -----------------
@router.post("/roles/{rol_id}/aplicaciones/{aplicacion_id}")
def asignar_aplicacion_a_rol(rol_id: int, aplicacion_id: int, session: Session = Depends(get_session)):
    """Asigna una aplicación a un rol"""
    try:
        aplicacion_rol = crud_aplicacion_rol.asignar_aplicacion_a_rol(session, aplicacion_id, rol_id)
        return {"message": "Aplicación asignada al rol"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al asignar aplicación: {str(e)}")

@router.delete("/roles/{rol_id}/aplicaciones/{aplicacion_id}")
def desasignar_aplicacion_de_rol(rol_id: int, aplicacion_id: int, session: Session = Depends(get_session)):
    """Desasigna una aplicación de un rol"""
    try:
        eliminado = crud_aplicacion_rol.desasignar_aplicacion_de_rol(session, aplicacion_id, rol_id)
        if eliminado:
            return {"message": "Aplicación desasignada del rol"}
        else:
            raise HTTPException(status_code=404, detail="No se encontró la asignación")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desasignar aplicación: {str(e)}")