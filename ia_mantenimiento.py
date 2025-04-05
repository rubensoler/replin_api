# ia_mantenimiento.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import json

# Importaciones actualizadas para la nueva versión de LangChain
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

router = APIRouter()

# Modelo de datos para la solicitud de procedimiento
class PasoMantenimiento(BaseModel):
    titulo: str
    descripcion: str
    notas: Optional[str] = None

class ProcedimientoResponse(BaseModel):
    pasos: List[PasoMantenimiento]
    precauciones: str
    herramientas: str

class SolicitudProcedimiento(BaseModel):
    tipo_equipo: str
    marca: Optional[str] = "Genérico"
    modelo: Optional[str] = "Genérico"

# Template para la generación de procedimientos de mantenimiento
procedimiento_template = PromptTemplate(
    input_variables=["tipo_equipo", "marca", "modelo"],
    template="""
    Eres un experto en mantenimiento industrial especializado en {tipo_equipo}. Genera un procedimiento detallado de mantenimiento preventivo para el siguiente equipo:
    
    Tipo de Equipo: {tipo_equipo}
    Marca: {marca}
    Modelo: {modelo}
    
    El procedimiento debe incluir:
    1. Pasos detallados con sus títulos y descripciones
    2. Precauciones de seguridad específicas para este tipo de equipo
    3. Herramientas necesarias para realizar el mantenimiento
    
    Asegúrate de que el procedimiento sea técnicamente correcto, siga las mejores prácticas de la industria y sea específico para este tipo de equipo.
    Devuelve la respuesta en formato JSON con la siguiente estructura:
    
    ```json
    {{
        "pasos": [
            {{
                "titulo": "Título del paso",
                "descripcion": "Descripción detallada",
                "notas": "Notas adicionales (opcional)"
            }}
        ],
        "precauciones": "Texto con precauciones de seguridad",
        "herramientas": "Lista de herramientas necesarias"
    }}
    ```
    
    Solo devuelve el JSON, sin texto adicional.
    """
)

@router.post("/api/generar-procedimiento/", response_model=ProcedimientoResponse)
async def generar_procedimiento(solicitud: SolicitudProcedimiento):
    try:
        # Obtener API key de OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="API key no configurada")
        
        # Configurar el modelo de lenguaje
        llm = ChatOpenAI(temperature=0.2, model="gpt-4o", api_key=api_key)
        
        # Crear la cadena para generar el procedimiento
        chain = LLMChain(
            llm=llm,
            prompt=procedimiento_template
        )
        
        # Generar el procedimiento
        resultado = chain.run(
            tipo_equipo=solicitud.tipo_equipo,
            marca=solicitud.marca,
            modelo=solicitud.modelo
        )
        
        # Parsear el resultado JSON
        # Eliminar posibles backticks y marcadores de código que pueda incluir el LLM
        resultado_limpio = resultado.replace("```json", "").replace("```", "").strip()
        procedimiento = json.loads(resultado_limpio)
        
        return procedimiento
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en formato JSON: {str(e)}. Respuesta: {resultado_limpio}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando el procedimiento: {str(e)}"
        )