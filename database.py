from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os
# CARGAR VARIABLES DE ENTORNO DESDE EL ARCHIVO .env
load_dotenv()
# BASE DE DATOS EN SQLITE
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

engine = create_engine(
    DATABASE_URL, 
    echo=True,  # MUESTRA LAS CONCULTAS SQL EN LA CONSOLA
    connect_args={"check_same_thread": False}
)

# CREACIÓN DE TABLAS EN LA BASE DE DATOS
def create_db_and_tables():
    from models import Categoria, Producto  # IMPORTAR MODELOS AQUÍ
    SQLModel.metadata.create_all(engine)
    print ("Tablas creadas correctamente.")

# FUNCIÓN PARA OBTENER UNA SESIÓN DE BASE DE DATOS
def get_session():
    with Session(engine) as session:
        yield session