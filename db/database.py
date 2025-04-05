"""
Configuración de la base de datos para la aplicación GAME.
"""
from sqlmodel import create_engine, Session, SQLModel

# Configuración de la base de datos
DATABASE_URL = "sqlite:///db.db"
engine = create_engine(DATABASE_URL, echo=True)

def create_db():
    """Crea todas las tablas definidas en los modelos"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Genera una sesión de base de datos para su uso en dependencias de FastAPI"""
    with Session(engine) as session:
        yield session