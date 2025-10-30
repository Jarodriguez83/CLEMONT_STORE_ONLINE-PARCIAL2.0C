from sqlmodel import create_engine, Session, SQLModel #CREATE_ENGINE: Para crear el motor de la base de datos, Session: Para manejar sesiones de trabajo temporal de DB, SQLModel: Clase base para modelos
from typing import Generator #GENERATOR: Sirve para indicar que una función no devuelve un valor normal, sino que "genera" valores de forma secuencial usando yield.
import os #OPERATING SYSTEM: Para manejar variables de entorno y rutas del sistema operativo

#CONFIGURACIÓN DE LA BASE DE DATOS
# Usar variable de entorno si existe, si no, usa el valor por defecto
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///database.db")
# check_same_thread=False es OBLIGATORIO para SQLite en entorno asíncrono (FastAPI)
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
# Funciones de Utilidad y Dependencia de FastAPI
def create_db_and_tables(engine_instance=engine):
    #CREA LA BASE DE DATOS Y LAS TABLAS DEFINIDAS EN LOS MODELOS SI NO EXISTEN
    SQLModel.metadata.create_all(engine_instance)
    print("BASE DE DATOS Y TABLAS CREADAS EXITOSAMENTE.")
def get_db_engine():
    #RETORNA EL MOTOR
    return engine
def get_session() -> Generator[Session, None, None]:
    #PROPORCIONA UNA SESIÓN DE BASE DE DATOS PARA CADA PETICIÓN Y HACE EL CIERRE AUTOMÁTICO
    with Session(engine) as session:
        yield session