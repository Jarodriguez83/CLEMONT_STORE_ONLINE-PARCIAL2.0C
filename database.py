# CLEMONT_STORE_ONLINE/database.py

from sqlmodel import create_engine, Session, SQLModel
from typing import Generator
import os

# --- Configuración de la Base de Datos ---

# Usar variable de entorno si existe, si no, usa el valor por defecto
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///database.db")

# Creación del Motor. 'echo=True' para ver las consultas SQL en desarrollo.
# check_same_thread=False es OBLIGATORIO para SQLite en entorno asíncrono (FastAPI)
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})


# --- Funciones de Utilidad y Dependencia de FastAPI ---

def create_db_and_tables(engine_instance=engine):
    """ Crea las tablas si no existen. """
    SQLModel.metadata.create_all(engine_instance)
    print("Base de datos y tablas creadas exitosamente.")

def get_db_engine():
    """ Retorna el motor. """
    return engine

def get_session() -> Generator[Session, None, None]:
    """
    Dependencia de FastAPI. Proporciona una sesión y asegura su cierre al finalizar la solicitud.
    """
    with Session(engine) as session:
        yield session