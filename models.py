from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class CategoriaBase(SQLModel):
    nombre: str = Field(index=True, unique=True, description="Nombre de la categoría")
    descripcion: Optional[str] = None