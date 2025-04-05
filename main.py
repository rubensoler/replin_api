"""
Punto de entrada principal para la aplicación GAME (Gestión de Activos y Mantenimiento de Equipos)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Importar la configuración de base de datos
from db import create_db

# Importar el router de IA para mantenimiento
from ia_mantenimiento import router as ia_mantenimiento_router

# Importar todos los routers modularizados
from routers import (
    equipment_router,
    organization_router,
    operations_router,
    business_router,
    users_router,
    llamaindex_router
)

# Importar configuración de ambiente
from dotenv import load_dotenv
load_dotenv()

# ----------------- INICIALIZACIÓN DE APP -----------------

app = FastAPI(
    title="GAME API", 
    description="API para la Gestión de Activos y Mantenimiento de Equipos",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    """Ejecuta acciones al iniciar la aplicación"""
    create_db()
    # Asegurar que existen los directorios necesarios
    os.makedirs("assets/cvs", exist_ok=True)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar carpeta de assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Incluir todos los routers
app.include_router(ia_mantenimiento_router, tags=["IA"])
app.include_router(equipment_router)
app.include_router(organization_router)
app.include_router(operations_router)
app.include_router(business_router)
app.include_router(users_router)
app.include_router(llamaindex_router)

@app.get("/api/health")
def health_check():
    """Verifica el estado de la API"""
    return {"status": "online", "message": "GAME API está funcionando correctamente"}

# Punto de entrada para pruebas de ejecución directas
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)