from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import SQLModel, Field, Session, create_engine, select, Relationship
from sqlalchemy.orm import joinedload
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, get_type_hints
from datetime import date
from io import BytesIO
import pandas as pd
from fastapi.staticfiles import StaticFiles
import os
from fastapi import UploadFile, File, HTTPException
import shutil
from fastapi import APIRouter
# llamaindex y chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, ServiceContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.ingestion import IngestionPipeline

import chromadb

# Importar el router de IA para mantenimiento
from ia_mantenimiento import router as ia_mantenimiento_router


from dotenv import load_dotenv
load_dotenv()
# ----------------- MODELOS -----------------

# ----------------- CARGOS Y PERSONAS -----------------

class Cargo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    descripcion: str = Field(max_length=50)
    personas: List["Persona"] = Relationship(back_populates="cargo")

class Persona(SQLModel, table=True):
    identificacion: int = Field(primary_key=True)
    nombres: str = Field(max_length=100)
    cargo_id: Optional[int] = Field(default=None, foreign_key="cargo.id")
    cargo: Optional[Cargo] = Relationship(back_populates="personas")
    actividades: List["Actividad"] = Relationship(back_populates="persona")

# ----------------- EQUIPOS CON NUEVA RELACION -----------------

class EquipoBase(SQLModel):
    nombre: str
    ubicacion: Optional[str] = None
    imagen: Optional[str] = Field(default=None, max_length=20, description="Nombre del archivo de imagen")

class Equipo(EquipoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subsistema_id: int = Field(foreign_key="subsistema.id")
    tipo_activo_id: int = Field(foreign_key="tipoactivo.id")

    actividades: List["Actividad"] = Relationship(back_populates="equipo")
    subsistema: Optional["SubSistema"] = Relationship(back_populates="equipos")
    tipo_activo: Optional["TipoActivo"] = Relationship()

class EquipoReadDetallado(SQLModel):
    id: int
    nombre: str
    ubicacion: Optional[str]
    imagen: Optional[str]
    subsistema_id: int
    tipo_activo_id: int
    subsistema: Optional["SubSistema"]
    tipo_activo: Optional["TipoActivo"]

class EquipoCreate(EquipoBase):
    subsistema_id: int
    tipo_activo_id: int  # ✅ Agregado

class EquipoUpdate(SQLModel):
    nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    imagen: Optional[str] = Field(default=None, max_length=20)
    subsistema_id: Optional[int] = None
    tipo_activo_id: Optional[int] = None  # ✅ Agregado
# ----------------- ACTIVIDADES -----------------

class ActividadBase(SQLModel):
    descripcion: str = Field(max_length=40, description="Máximo 40 caracteres")
    fecha: date

class Actividad(ActividadBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    equipo_id: int = Field(foreign_key="equipo.id")
    persona_id: int = Field(foreign_key="persona.identificacion")
    equipo: Optional[Equipo] = Relationship(back_populates="actividades")
    persona: Optional[Persona] = Relationship(back_populates="actividades")

class ActividadCreate(ActividadBase):
    equipo_id: int
    persona_id: int

class ActividadUpdate(SQLModel):
    descripcion: Optional[str] = Field(default=None, max_length=40)
    fecha: Optional[date] = None
    equipo_id: Optional[int] = None
    persona_id: Optional[int] = None

class ActividadRead(ActividadBase):
    id: int
    equipo_id: int
    persona_id: int

class EquipoRead(EquipoBase):
    id: int

class ActividadDetallada(SQLModel):
    id: int
    fecha: date
    descripcion: str
    persona: str
    cargo: Optional[str]
    equipo: str

# ----------------- ESTRUCTURA PLANTA - SISTEMA - SUBSISTEMA -----------------

class Sistema(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(max_length=20)
    nombre: str
    descripcion: Optional[str] = None 
    planta_id: int = Field(foreign_key="planta.id")

    planta: Optional["Planta"] = Relationship(back_populates="sistemas")
    subsistemas: List["SubSistema"] = Relationship(back_populates="sistema")

class SubSistema(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(max_length=20)
    nombre: str
    descripcion: Optional[str] = None 
    sistema_id: int = Field(foreign_key="sistema.id")

    sistema: Optional["Sistema"] = Relationship(back_populates="subsistemas")
    equipos: List[Equipo] = Relationship(back_populates="subsistema")

# ----------------- USUARIOS Y AUTENTICACION -----------------

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str
    email: Optional[str] = None
    rol_id: int = Field(foreign_key="rol.id")
    rol: "Rol" = Relationship(back_populates="usuarios")
    contratos: List["ContratoUsuario"] = Relationship(back_populates="usuario")

class Rol(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    descripcion: str
    usuarios: List[Usuario] = Relationship(back_populates="rol")
    aplicaciones: List["AplicacionRol"] = Relationship(back_populates="rol")

class Aplicacion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    roles: List["AplicacionRol"] = Relationship(back_populates="aplicacion")

class AplicacionRol(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rol_id: int = Field(foreign_key="rol.id")
    aplicacion_id: int = Field(foreign_key="aplicacion.id")
    rol: "Rol" = Relationship(back_populates="aplicaciones")
    aplicacion: "Aplicacion" = Relationship(back_populates="roles")

# ----------------- CONTRATOS Y CLIENTES -----------------

class Contrato(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    cliente_id: int = Field(foreign_key="cliente.id")
    cliente: "Cliente" = Relationship(back_populates="contratos")
    plantas: List["Planta"] = Relationship(back_populates="contrato")
    contratos_usuarios: List["ContratoUsuario"] = Relationship(back_populates="contrato")

class ContratoUsuario(SQLModel, table=True):
    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
    contrato_id: int = Field(foreign_key="contrato.id", primary_key=True)
    usuario: Usuario = Relationship(back_populates="contratos")
    contrato: Contrato = Relationship(back_populates="contratos_usuarios")

class Cliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    contratos: List[Contrato] = Relationship(back_populates="cliente")

# ----------------- PLANTA (MODIFICADA PARA INCLUIR SISTEMAS) -----------------

class Planta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    municipio: str
    localizacion: Optional[str] = None  # GPS
    contrato_id: int = Field(foreign_key="contrato.id")
    contrato: Contrato = Relationship(back_populates="plantas")
    sistemas: List[Sistema] = Relationship(back_populates="planta")


# ----------------- TIPO DE ACTIVOS -----------------
class TipoActivoBase(SQLModel):
    descripcion: str
    imagen: Optional[str] = None

class TipoActivo(TipoActivoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class TipoActivoCreate(TipoActivoBase):
    pass

class TipoActivoRead(TipoActivoBase):
    id: int

class TipoActivoUpdate(SQLModel):
    descripcion: Optional[str] = None
    imagen: Optional[str] = None

# ----------------- MODELO JERARQUICO PARA /plantas_jerarquia -----------------

class EquipoReadMini(SQLModel):
    id: int
    nombre: str

class SubSistemaRead(SQLModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str 
    equipos: List[EquipoReadMini] = []

class SistemaRead(SQLModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str
    subsistemas: List[SubSistemaRead] = []

class PlantaJerarquica(SQLModel):
    id: int
    nombre: str
    municipio: str
    localizacion: Optional[str] = None
    sistemas: List[SistemaRead] = []
# ----------------- DB CONFIG -----------------

DATABASE_URL = "sqlite:///db.db"
engine = create_engine(DATABASE_URL, echo=True)

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# ----------------- APP -----------------

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crea el directorio si no existe
os.makedirs("assets/cvs", exist_ok=True)

# Monta la carpeta de assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


# Incluir el router de IA para mantenimiento
app.include_router(ia_mantenimiento_router, tags=["IA"])

# ----------------- ENDPOINTS -----------------

# Ruta para probar la conexión con el servicio de IA
@app.get("/api/ia/status")
def ia_status():
    return {"status": "online", "message": "Servicio de IA para mantenimiento disponible"}

@app.post("/cargos/", response_model=Cargo)
def crear_cargo(cargo: Cargo, session: Session = Depends(get_session)):
    session.add(cargo)
    session.commit()
    session.refresh(cargo)
    return cargo

@app.get("/cargos/", response_model=List[Cargo])
def listar_cargos(session: Session = Depends(get_session)):
    return session.exec(select(Cargo)).all()

@app.put("/cargos/{cargo_id}", response_model=Cargo)
def actualizar_cargo(cargo_id: int, cargo_data: Cargo, session: Session = Depends(get_session)):
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo no encontrado")
    for key, value in cargo_data.dict(exclude_unset=True).items():
        setattr(cargo, key, value)
    session.add(cargo)
    session.commit()
    session.refresh(cargo)
    return cargo

@app.delete("/cargos/{cargo_id}")
def eliminar_cargo(cargo_id: int, session: Session = Depends(get_session)):
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo no encontrado")
    session.delete(cargo)
    session.commit()
    return {"ok": True}

@app.post("/personas/", response_model=Persona)
def crear_persona(persona: Persona, session: Session = Depends(get_session)):
    session.add(persona)
    session.commit()
    session.refresh(persona)
    return persona

@app.get("/personas/", response_model=List[Persona])
def listar_personas(session: Session = Depends(get_session)):
    return session.exec(select(Persona)).all()

@app.put("/personas/{identificacion}", response_model=Persona)
def actualizar_persona(identificacion: int, persona_data: Persona, session: Session = Depends(get_session)):
    persona = session.get(Persona, identificacion)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    for key, value in persona_data.dict(exclude_unset=True).items():
        setattr(persona, key, value)
    session.add(persona)
    session.commit()
    session.refresh(persona)
    return persona

@app.delete("/personas/{identificacion}")
def eliminar_persona(identificacion: int, session: Session = Depends(get_session)):
    persona = session.get(Persona, identificacion)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    session.delete(persona)
    session.commit()
    return {"ok": True}

@app.post("/equipos/", response_model=EquipoRead)
def crear_equipo(equipo: EquipoCreate, session: Session = Depends(get_session)):
    nuevo = Equipo.from_orm(equipo)
    session.add(nuevo)
    session.commit()
    session.refresh(nuevo)
    return nuevo

@app.get("/equipos/", response_model=List[EquipoReadDetallado])
def listar_equipos(session: Session = Depends(get_session)):
    return session.exec(select(Equipo).options(joinedload(Equipo.subsistema), joinedload(Equipo.tipo_activo))).all()


@app.put("/equipos/{equipo_id}", response_model=EquipoRead)
def actualizar_equipo(equipo_id: int, equipo_data: EquipoUpdate, session: Session = Depends(get_session)):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    for key, value in equipo_data.dict(exclude_unset=True).items():
        setattr(equipo, key, value)
    session.add(equipo)
    session.commit()
    session.refresh(equipo)
    return equipo

@app.delete("/equipos/{equipo_id}")
def eliminar_equipo(equipo_id: int, session: Session = Depends(get_session)):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    session.delete(equipo)
    session.commit()
    return {"ok": True}

@app.post("/actividades/", response_model=ActividadRead)
def crear_actividad(actividad: ActividadCreate, session: Session = Depends(get_session)):
    if not session.get(Equipo, actividad.equipo_id):
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    if not session.get(Persona, actividad.persona_id):
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    nueva = Actividad.from_orm(actividad)
    session.add(nueva)
    session.commit()
    session.refresh(nueva)
    return nueva

@app.get("/actividades/", response_model=List[ActividadRead])
def listar_actividades(session: Session = Depends(get_session)):
    return session.exec(select(Actividad)).all()

@app.put("/actividades/{actividad_id}", response_model=ActividadRead)
def actualizar_actividad(actividad_id: int, actividad_data: ActividadUpdate, session: Session = Depends(get_session)):
    actividad = session.get(Actividad, actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    for key, value in actividad_data.dict(exclude_unset=True).items():
        setattr(actividad, key, value)
    session.add(actividad)
    session.commit()
    session.refresh(actividad)
    return actividad

@app.delete("/actividades/{actividad_id}")
def eliminar_actividad(actividad_id: int, session: Session = Depends(get_session)):
    actividad = session.get(Actividad, actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    session.delete(actividad)
    session.commit()
    return {"ok": True}

@app.get("/actividades/detalladas/", response_model=List[ActividadDetallada])
def listar_actividades_detalladas(
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    persona_id: Optional[int] = Query(None),
    equipo_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    stmt = select(Actividad).options(
        joinedload(Actividad.persona).joinedload(Persona.cargo),
        joinedload(Actividad.equipo)
    )
    if desde:
        stmt = stmt.where(Actividad.fecha >= desde)
    if hasta:
        stmt = stmt.where(Actividad.fecha <= hasta)
    if persona_id:
        stmt = stmt.where(Actividad.persona_id == persona_id)
    if equipo_id:
        stmt = stmt.where(Actividad.equipo_id == equipo_id)

    actividades = session.exec(stmt).all()

    resultado = []
    for act in actividades:
        resultado.append(ActividadDetallada(
            id=act.id,  # 👈 Esto es lo que permite luego eliminar
            fecha=act.fecha,
            descripcion=act.descripcion,
            persona=act.persona.nombres,
            cargo=act.persona.cargo.descripcion if act.persona.cargo else None,
            equipo=act.equipo.nombre
        ))
    return resultado

@app.get("/actividades/exportar/")
def exportar_actividades_detalladas(
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    persona_id: Optional[int] = Query(None),
    equipo_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    stmt = select(Actividad).options(
        joinedload(Actividad.persona).joinedload(Persona.cargo),
        joinedload(Actividad.equipo)
    )
    if desde:
        stmt = stmt.where(Actividad.fecha >= desde)
    if hasta:
        stmt = stmt.where(Actividad.fecha <= hasta)
    if persona_id:
        stmt = stmt.where(Actividad.persona_id == persona_id)
    if equipo_id:
        stmt = stmt.where(Actividad.equipo_id == equipo_id)
    actividades = session.exec(stmt).all()
    data = []
    for act in actividades:
        data.append({
            "Fecha": act.fecha.strftime("%Y-%m-%d"),
            "Descripción": act.descripcion,
            "Persona": act.persona.nombres,
            "Cargo": act.persona.cargo.descripcion if act.persona.cargo else None,
            "Equipo": act.equipo.nombre
        })
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Actividades')
    output.seek(0)
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": "attachment; filename=actividades.xlsx"}
    )

# Mapear nombres de tabla a modelos
MODELOS = {
    "cargos": Cargo,
    "personas": Persona,
    "equipos": Equipo,
    # Agrega más aquí si deseas
}

@app.post("/cargue_masivo/{tabla}")
def cargue_masivo(tabla: str, file: UploadFile = File(...), session: Session = Depends(get_session)):
    if tabla not in MODELOS:
        raise HTTPException(status_code=400, detail=f"La tabla '{tabla}' no está soportada.")

    Modelo = MODELOS[tabla]

    try:
        contenido = file.file.read()
        df = pd.read_excel(BytesIO(contenido), sheet_name=0)

        campos_modelo = [c for c in get_type_hints(Modelo).keys() if not c.startswith("_")]
        columnas_excel = df.columns.tolist()
        columnas_validas = [col for col in columnas_excel if col in campos_modelo]

        if not columnas_validas:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo no contiene columnas válidas para la tabla '{tabla}'. Esperadas: {campos_modelo}"
            )

        # Detectar campo clave primaria real de la tabla
        pk_column = list(Modelo.__table__.primary_key.columns)[0]
        pk = pk_column.name

        registros_insertados = 0
        registros_omitidos = 0

        for _, row in df.iterrows():
            datos = {
                col: row[col]
                for col in columnas_validas
                if col in row and not pd.isna(row[col])
            }

            if not datos:
                continue

            # Conversión simple para enteros
            for campo, tipo in get_type_hints(Modelo).items():
                if campo in datos and tipo == int:
                    try:
                        datos[campo] = int(datos[campo])
                    except:
                        pass

            # Validar duplicado por clave primaria
            if pk and pk in datos:
                existente = session.get(Modelo, datos[pk])
                if existente:
                    registros_omitidos += 1
                    continue

            session.add(Modelo(**datos))
            registros_insertados += 1

        session.commit()

        return {
            "message": f"Cargue exitoso en '{tabla}'",
            "registros_insertados": registros_insertados,
            "registros_omitidos": registros_omitidos,
            "columnas_usadas": columnas_validas
        }

    except Exception as e:
        print("Error en cargue masivo:", str(e))
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")
    

@app.get("/verificar_cv/{persona_id}")
def verificar_cv(persona_id: int):
    filename = f"assets/cvs/{persona_id}-101.pdf"
    existe = os.path.isfile(filename)
    return {"exists": existe}


@app.post("/upload_cv/{persona_id}")
def upload_cv(persona_id: int, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    filename = f"assets/cvs/{persona_id}-101.pdf"
    os.makedirs("assets/cvs", exist_ok=True)

    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": "Archivo cargado con éxito"}




# ----------------- LlamaIndex Endpoints -----------------
@app.get("/listar_cvs")
def listar_cvs():
    carpeta = "assets/cvs"
    if not os.path.exists(carpeta):
        print("❌ Carpeta no existe:", os.getcwd())  # Debug
        raise HTTPException(status_code=404, detail="La carpeta de CVs no existe")
    
    archivos = [f for f in os.listdir(carpeta) if f.endswith(".pdf")]
    print("📄 Archivos encontrados:", archivos)  # Debug
    return {"archivos": archivos}


@app.post("/indexar_cvs")
def indexar_cvs():
    carpeta = "assets/cvs"
    archivos = [f for f in os.listdir(carpeta) if f.endswith(".pdf")]

    print("Archivos encontrados:", archivos)

    if not archivos:
        raise HTTPException(status_code=404, detail="No hay archivos PDF para indexar.")

    try:
        db = chromadb.PersistentClient(path="chroma")
        vector_store = ChromaVectorStore(chroma_collection=db.get_or_create_collection("curriculums"))
        pipeline = IngestionPipeline(transformations=[SimpleNodeParser()])

        documents = SimpleDirectoryReader(input_dir=carpeta, required_exts=[".pdf"]).load_data()

        # ✅ Obtener nombres de archivo
        document_names = [doc.metadata.get('file_path', 'sin_nombre') for doc in documents]

        if not documents:
            raise HTTPException(status_code=400, detail="No se pudieron cargar documentos con llamaindex.")

        nodes = pipeline.run(documents=documents)
        index = VectorStoreIndex(nodes, storage_context=StorageContext.from_defaults(vector_store=vector_store))

        # ✅ Retornar detalle
        return {
            "message": f"Se indexaron {len(nodes)} nodos desde {len(documents)} documentos.",
            "documentos_indexados": document_names
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/consultar")
def consultar_llamaindex(pregunta: str):
    try:
        db = chromadb.PersistentClient(path="chroma")
        vector_store = ChromaVectorStore(chroma_collection=db.get_or_create_collection("curriculums"))
        index = VectorStoreIndex.from_vector_store(vector_store)
        engine = index.as_query_engine()
        respuesta = engine.query(pregunta)
        return {"respuesta": str(respuesta)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar: {str(e)}")


# ----------------- ROL -----------------
# Crear un nuevo rol
@app.post("/roles/", response_model=Rol)
def crear_rol(rol: Rol, session: Session = Depends(get_session)):
    session.add(rol)
    session.commit()
    session.refresh(rol)
    return rol

# Listar todos los roles
@app.get("/roles/", response_model=List[Rol])
def listar_roles(session: Session = Depends(get_session)):
    return session.exec(select(Rol)).all()

# Actualizar un rol
@app.put("/roles/{rol_id}", response_model=Rol)
def actualizar_rol(rol_id: int, rol_data: Rol, session: Session = Depends(get_session)):
    rol = session.get(Rol, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    for key, value in rol_data.dict(exclude_unset=True).items():
        setattr(rol, key, value)
    session.add(rol)
    session.commit()
    session.refresh(rol)
    return rol

# Eliminar un rol
@app.delete("/roles/{rol_id}")
def eliminar_rol(rol_id: int, session: Session = Depends(get_session)):
    rol = session.get(Rol, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    session.delete(rol)
    session.commit()
    return {"ok": True}

# ----------------- USUARIO -----------------

# Crear un nuevo usuario
@app.post("/usuarios/", response_model=Usuario)
def crear_usuario(usuario: Usuario, session: Session = Depends(get_session)):
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

# Listar todos los usuarios
@app.get("/usuarios/", response_model=List[Usuario])
def listar_usuarios(session: Session = Depends(get_session)):
    return session.exec(select(Usuario)).all()

# Actualizar un usuario
@app.put("/usuarios/{usuario_id}", response_model=Usuario)
def actualizar_usuario(usuario_id: int, usuario_data: Usuario, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for key, value in usuario_data.dict(exclude_unset=True).items():
        setattr(usuario, key, value)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

# Eliminar un usuario
@app.delete("/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    session.delete(usuario)
    session.commit()
    return {"ok": True}

# ----------------- CONTRATO -----------------

# Crear un nuevo contrato
@app.post("/contratos/", response_model=Contrato)
def crear_contrato(contrato: Contrato, session: Session = Depends(get_session)):
    session.add(contrato)
    session.commit()
    session.refresh(contrato)
    return contrato

# Listar todos los contratos
@app.get("/contratos/")
def listar_contratos(session: Session = Depends(get_session)):
    contratos = session.exec(select(Contrato)).all()
    for contrato in contratos:
        contrato.plantas  # fuerza la carga de la relación si es lazy
    return contratos

# Actualizar un contrato
@app.put("/contratos/{contrato_id}", response_model=Contrato)
def actualizar_contrato(contrato_id: int, contrato_data: Contrato, session: Session = Depends(get_session)):
    contrato = session.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    for key, value in contrato_data.dict(exclude_unset=True).items():
        setattr(contrato, key, value)
    session.add(contrato)
    session.commit()
    session.refresh(contrato)
    return contrato

# Eliminar un contrato
@app.delete("/contratos/{contrato_id}")
def eliminar_contrato(contrato_id: int, session: Session = Depends(get_session)):
    contrato = session.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    session.delete(contrato)
    session.commit()
    return {"ok": True}

# ----------------- ASIGNAR CONTRATO A USUARIO -----------------

# Asignar contrato a usuario
@app.post("/usuarios/{usuario_id}/contratos/{contrato_id}")
def asignar_contrato_a_usuario(usuario_id: int, contrato_id: int, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, usuario_id)
    contrato = session.get(Contrato, contrato_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    contrato_usuario = ContratoUsuario(usuario_id=usuario_id, contrato_id=contrato_id)
    session.add(contrato_usuario)
    session.commit()
    return {"message": "Contrato asignado al usuario"}

# ----------------- APLICACION -----------------

# Crear una nueva aplicación
@app.post("/aplicaciones/", response_model=Aplicacion)
def crear_aplicacion(aplicacion: Aplicacion, session: Session = Depends(get_session)):
    session.add(aplicacion)
    session.commit()
    session.refresh(aplicacion)
    return aplicacion

# Listar todas las aplicaciones
@app.get("/aplicaciones/", response_model=List[Aplicacion])
def listar_aplicaciones(session: Session = Depends(get_session)):
    return session.exec(select(Aplicacion)).all()

# Actualizar una aplicación
@app.put("/aplicaciones/{aplicacion_id}", response_model=Aplicacion)
def actualizar_aplicacion(aplicacion_id: int, aplicacion_data: Aplicacion, session: Session = Depends(get_session)):
    aplicacion = session.get(Aplicacion, aplicacion_id)
    if not aplicacion:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    for key, value in aplicacion_data.dict(exclude_unset=True).items():
        setattr(aplicacion, key, value)
    session.add(aplicacion)
    session.commit()
    session.refresh(aplicacion)
    return aplicacion

# Eliminar una aplicación
@app.delete("/aplicaciones/{aplicacion_id}")
def eliminar_aplicacion(aplicacion_id: int, session: Session = Depends(get_session)):
    aplicacion = session.get(Aplicacion, aplicacion_id)
    if not aplicacion:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    session.delete(aplicacion)
    session.commit()
    return {"ok": True}

# ----------------- ASIGNAR ROL A USUARIO -----------------

# Asignar rol a usuario
@app.post("/usuarios/{usuario_id}/rol/{rol_id}")
def asignar_rol_a_usuario(usuario_id: int, rol_id: int, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, usuario_id)
    rol = session.get(Rol, rol_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    usuario.rol_id = rol_id
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return {"message": "Rol asignado al usuario"}

# ----------------- ASIGNAR APLICACION A ROL -----------------

# Asignar aplicación a rol
@app.post("/roles/{rol_id}/aplicaciones/{aplicacion_id}")
def asignar_aplicacion_a_rol(rol_id: int, aplicacion_id: int, session: Session = Depends(get_session)):
    rol = session.get(Rol, rol_id)
    aplicacion = session.get(Aplicacion, aplicacion_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if not aplicacion:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    aplicacion_rol = AplicacionRol(rol_id=rol_id, aplicacion_id=aplicacion_id)
    session.add(aplicacion_rol)
    session.commit()
    return {"message": "Aplicación asignada al rol"}


# ----------------- CLIENTES -----------------
@app.post("/clientes/", response_model=Cliente)
def crear_cliente(cliente: Cliente, session: Session = Depends(get_session)):
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente

@app.get("/clientes/", response_model=List[Cliente])
def listar_clientes(session: Session = Depends(get_session)):
    return session.exec(select(Cliente)).all()

@app.put("/clientes/{cliente_id}", response_model=Cliente)
def actualizar_cliente(cliente_id: int, cliente_data: Cliente, session: Session = Depends(get_session)):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for key, value in cliente_data.dict(exclude_unset=True).items():
        setattr(cliente, key, value)
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente

@app.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, session: Session = Depends(get_session)):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    session.delete(cliente)
    session.commit()
    return {"ok": True}

# ----------------- PLANTAS -----------------
@app.post("/plantas/", response_model=Planta)
def crear_planta(planta: Planta, session: Session = Depends(get_session)):
    session.add(planta)
    session.commit()
    session.refresh(planta)
    return planta

@app.get("/plantas/", response_model=List[Planta])
def listar_plantas(session: Session = Depends(get_session)):
    return session.exec(select(Planta)).all()

@app.put("/plantas/{planta_id}", response_model=Planta)
def actualizar_planta(planta_id: int, planta_data: Planta, session: Session = Depends(get_session)):
    planta = session.get(Planta, planta_id)
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    for key, value in planta_data.dict(exclude_unset=True).items():
        setattr(planta, key, value)
    session.add(planta)
    session.commit()
    session.refresh(planta)
    return planta

@app.delete("/plantas/{planta_id}")
def eliminar_planta(planta_id: int, session: Session = Depends(get_session)):
    planta = session.get(Planta, planta_id)
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    session.delete(planta)
    session.commit()
    return {"ok": True}

@app.get("/clientes/{cliente_id}/contratos", response_model=List[Contrato])
def obtener_contratos_cliente(cliente_id: int, session: Session = Depends(get_session)):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente.contratos


@app.post("/clientes/{cliente_id}/contratos/{contrato_id}", response_model=Contrato)
def asignar_contrato_a_cliente(cliente_id: int, contrato_id: int, session: Session = Depends(get_session)):
    cliente = session.get(Cliente, cliente_id)
    contrato = session.get(Contrato, contrato_id)
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    contrato.cliente_id = cliente_id
    session.add(contrato)
    session.commit()
    session.refresh(contrato)
    return contrato


@app.delete("/clientes/{cliente_id}/contratos/{contrato_id}")
def eliminar_contrato_cliente(cliente_id: int, contrato_id: int, session: Session = Depends(get_session)):
    contrato = session.get(Contrato, contrato_id)
    
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if contrato.cliente_id != cliente_id:
        raise HTTPException(status_code=400, detail="Este contrato no está asociado con el cliente especificado")
    
    contrato.cliente_id = None  # Desasociar el contrato del cliente
    session.add(contrato)
    session.commit()
    return {"ok": True}


@app.get("/plantas/{planta_id}/equipos", response_model=List[EquipoRead])
def obtener_equipos_planta(planta_id: int, session: Session = Depends(get_session)):
    planta = session.get(Planta, planta_id)
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    return planta.equipos


@app.get("/equipos/detallados/", response_model=List[EquipoReadDetallado])
def listar_equipos_detallados(session: Session = Depends(get_session)):
    stmt = select(Equipo).options(
        joinedload(Equipo.subsistema),
        joinedload(Equipo.tipo_activo)
    )
    return session.exec(stmt).all()



@app.post("/plantas/{planta_id}/equipos/{equipo_id}", response_model=EquipoRead)
def asignar_equipo_a_planta(planta_id: int, equipo_id: int, session: Session = Depends(get_session)):
    planta = session.get(Planta, planta_id)
    equipo = session.get(Equipo, equipo_id)
    
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    equipo.planta_id = planta_id  # Asignar planta al equipo
    session.add(equipo)
    session.commit()
    session.refresh(equipo)
    return equipo


@app.delete("/plantas/{planta_id}/equipos/{equipo_id}")
def eliminar_equipo_planta(planta_id: int, equipo_id: int, session: Session = Depends(get_session)):
    equipo = session.get(Equipo, equipo_id)
    
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    if equipo.planta_id != planta_id:
        raise HTTPException(status_code=400, detail="Este equipo no está asociado con la planta especificada")
    
    equipo.planta_id = None  # Desasociar el equipo de la planta
    session.add(equipo)
    session.commit()
    return {"ok": True}


# ENDPOINTS NUEVOS: SISTEMAS

@app.get("/sistemas/")
def listar_sistemas(session: Session = Depends(get_session)):
    return session.exec(select(Sistema)).all()

@app.post("/sistemas/")
def crear_sistema(sistema: Sistema, session: Session = Depends(get_session)):
    session.add(sistema)
    session.commit()
    session.refresh(sistema)
    return sistema

@app.put("/sistemas/{sistema_id}")
def actualizar_sistema(sistema_id: int, sistema_data: Sistema, session: Session = Depends(get_session)):
    sistema = session.get(Sistema, sistema_id)
    if not sistema:
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    sistema.codigo = sistema_data.codigo
    sistema.nombre = sistema_data.nombre
    sistema.planta_id = sistema_data.planta_id
    session.add(sistema)
    session.commit()
    return sistema

@app.delete("/sistemas/{sistema_id}")
def eliminar_sistema(sistema_id: int, session: Session = Depends(get_session)):
    sistema = session.get(Sistema, sistema_id)
    if not sistema:
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    session.delete(sistema)
    session.commit()
    return {"ok": True}

@app.get("/plantas/{planta_id}/sistemas", response_model=List[Sistema])
def obtener_sistemas_planta(planta_id: int, session: Session = Depends(get_session)):
    planta = session.get(Planta, planta_id)
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    return planta.sistemas

# ENDPOINTS NUEVOS: SUBSISTEMAS

@app.get("/subsistemas/")
def listar_subsistemas(session: Session = Depends(get_session)):
    return session.exec(select(SubSistema)).all()

@app.post("/subsistemas/")
def crear_subsistema(subsistema: SubSistema, session: Session = Depends(get_session)):
    session.add(subsistema)
    session.commit()
    session.refresh(subsistema)
    return subsistema

@app.put("/subsistemas/{subsistema_id}")
def actualizar_subsistema(subsistema_id: int, subsistema_data: SubSistema, session: Session = Depends(get_session)):
    subsistema = session.get(SubSistema, subsistema_id)
    if not subsistema:
        raise HTTPException(status_code=404, detail="SubSistema no encontrado")
    subsistema.codigo = subsistema_data.codigo
    subsistema.nombre = subsistema_data.nombre
    subsistema.sistema_id = subsistema_data.sistema_id
    session.add(subsistema)
    session.commit()
    return subsistema

@app.delete("/subsistemas/{subsistema_id}")
def eliminar_subsistema(subsistema_id: int, session: Session = Depends(get_session)):
    subsistema = session.get(SubSistema, subsistema_id)
    if not subsistema:
        raise HTTPException(status_code=404, detail="SubSistema no encontrado")
    session.delete(subsistema)
    session.commit()
    return {"ok": True}


@app.get("/plantas_jerarquia/", response_model=List[PlantaJerarquica])
def obtener_estructura_completa(session: Session = Depends(get_session)):
    plantas = session.exec(select(Planta)).all()
    for planta in plantas:
        planta.sistemas
        for sistema in planta.sistemas:
            sistema.subsistemas
            for subsistema in sistema.subsistemas:
                subsistema.equipos
    return plantas


# ----------------- NUEVOS ENDPOINTS DE JERARQUÍA -----------------

@app.get("/plantas/{planta_id}/sistemas", response_model=List[Sistema])
def obtener_sistemas_por_planta(planta_id: int, session: Session = Depends(get_session)):
    planta = session.get(Planta, planta_id)
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    return planta.sistemas

@app.get("/sistemas/{sistema_id}/subsistemas", response_model=List[SubSistema])
def obtener_subsistemas_por_sistema(sistema_id: int, session: Session = Depends(get_session)):
    sistema = session.get(Sistema, sistema_id)
    if not sistema:
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    return sistema.subsistemas

@app.get("/subsistemas/{subsistema_id}/equipos", response_model=List[Equipo])
def obtener_equipos_por_subsistema(subsistema_id: int, session: Session = Depends(get_session)):
    subsistema = session.get(SubSistema, subsistema_id)
    if not subsistema:
        raise HTTPException(status_code=404, detail="Subsistema no encontrado")
    return subsistema.equipos




# ----------------- NUEVOS ENDPOINTS DE TIPO ACTIVO -----------------
@app.post("/tipos-activo/", response_model=TipoActivoRead)
def crear_tipo_activo(tipo: TipoActivoCreate, session: Session = Depends(get_session)):
    nuevo = TipoActivo.from_orm(tipo)
    session.add(nuevo)
    session.commit()
    session.refresh(nuevo)
    return nuevo

@app.get("/tipos-activo/", response_model=list[TipoActivoRead])
def listar_tipos_activo(session: Session = Depends(get_session)):
    return session.exec(select(TipoActivo)).all()

@app.get("/tipos-activo/{tipo_id}", response_model=TipoActivoRead)
def obtener_tipo_activo(tipo_id: int, session: Session = Depends(get_session)):
    tipo = session.get(TipoActivo, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de activo no encontrado")
    return tipo

@app.put("/tipos-activo/{tipo_id}", response_model=TipoActivoRead)
def actualizar_tipo_activo(tipo_id: int, tipo_data: TipoActivoUpdate, session: Session = Depends(get_session)):
    tipo = session.get(TipoActivo, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de activo no encontrado")
    tipo_data_dict = tipo_data.dict(exclude_unset=True)
    for key, value in tipo_data_dict.items():
        setattr(tipo, key, value)
    session.commit()
    session.refresh(tipo)
    return tipo

@app.delete("/tipos-activo/{tipo_id}")
def eliminar_tipo_activo(tipo_id: int, session: Session = Depends(get_session)):
    tipo = session.get(TipoActivo, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de activo no encontrado")
    session.delete(tipo)
    session.commit()
    return {"ok": True}