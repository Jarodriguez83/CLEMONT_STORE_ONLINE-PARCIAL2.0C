from typing import Optional, List
from sqlmodel import SQLModel
from pydantic import Field

class CategoriaCrear(SQLModel): 
    nombre: str = Field (min_length=3, description="NOMBRE DE LA CATEGORIA")
    description: Optional[str] = Field (default=None)

class CategoriaLeer(SQLModel): 
    id: int 
    nombre: str
    description: Optional[str]
    activa: bool 

class CategoriaActualizar(SQLModel): 
    nombre: Optional[str]=None 
    description: Optional[str]=None
    activa: Optional[bool]=None


class ProductoCrear(SQLModel): 
    nombre: str = Field(min_length=3)
    description: Optional[str]=None
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)
    categoria_id:int

class ProductoLeer(SQLModel): 
    id: int
    nombre: str
    description: Optional[str]
    precio: float
    stock: int 
    activo: bool 
    categoria_id: int 

class ProductoActualizar(SQLModel):  
    nombre: Optional[str]=None
    description: Optional[str]=None
    precio= Optional[float]=None
    stock: Optional[bool]=None
    categoria_id: Optional[int]=None