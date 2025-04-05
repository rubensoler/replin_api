"""
Router para operaciones de búsqueda e indexación con LlamaIndex.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
import os
import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.ingestion import IngestionPipeline

from db import get_session

# Crear router
router = APIRouter(prefix="/api", tags=["Búsqueda e Indexación"])

@router.get("/listar_cvs")
def listar_cvs():
    """Lista todos los archivos PDF en la carpeta de CVs"""
    carpeta = "assets/cvs"
    if not os.path.exists(carpeta):
        print("❌ Carpeta no existe:", os.getcwd())  # Debug
        raise HTTPException(status_code=404, detail="La carpeta de CVs no existe")
    
    archivos = [f for f in os.listdir(carpeta) if f.endswith(".pdf")]
    print("📄 Archivos encontrados:", archivos)  # Debug
    return {"archivos": archivos}

@router.post("/indexar_cvs")
def indexar_cvs():
    """Indexa todos los archivos PDF en la carpeta de CVs"""
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

        # Obtener nombres de archivo
        document_names = [doc.metadata.get('file_path', 'sin_nombre') for doc in documents]

        if not documents:
            raise HTTPException(status_code=400, detail="No se pudieron cargar documentos con llamaindex.")

        nodes = pipeline.run(documents=documents)
        index = VectorStoreIndex(nodes, storage_context=StorageContext.from_defaults(vector_store=vector_store))

        # Retornar detalle
        return {
            "message": f"Se indexaron {len(nodes)} nodos desde {len(documents)} documentos.",
            "documentos_indexados": document_names
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consultar")
def consultar_llamaindex(pregunta: str):
    """Consulta el índice de documentos con una pregunta"""
    try:
        db = chromadb.PersistentClient(path="chroma")
        vector_store = ChromaVectorStore(chroma_collection=db.get_or_create_collection("curriculums"))
        index = VectorStoreIndex.from_vector_store(vector_store)
        engine = index.as_query_engine()
        respuesta = engine.query(pregunta)
        return {"respuesta": str(respuesta)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar: {str(e)}")