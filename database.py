# CLEMONT_STORE_ONLINE/database.py

from sqlmodel import create_engine, Session
import os
from typing import Generator

# ----------------------------------------------------------------------
# 1. Configuración del Motor de la Base de Datos
# ----------------------------------------------------------------------

# Define la URL de la base de datos.
# Usa una variable de entorno si existe, si no, usa el valor por defecto (sqlite:///database.db).
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///database.db")

# Creación del Motor. 'echo=True' es útil en desarrollo para ver las consultas SQL.
# 'connect_args={"check_same_thread": False}' es NECESARIO para SQLite con FastAPI.
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})


# ----------------------------------------------------------------------
# 2. Funciones de Utilidad y Dependencia de FastAPI
# ----------------------------------------------------------------------

def get_db_engine():
    """
    Retorna el motor de la base de datos.
    """
    return engine

def get_session() -> Generator[Session, None, None]:
    """
    Generador de dependencias de FastAPI.
    Proporciona una nueva sesión de DB y asegura su cierre (cierre automático por 'with Session').
    """
    with Session(engine) as session:
        yield session