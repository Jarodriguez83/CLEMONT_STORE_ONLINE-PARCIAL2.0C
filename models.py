from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class CategoriaBase(SQLModel):
    nombre: str = Field(index=True, unique=True, description="Nombre de la categoría")
    descripcion: Optional[str] = None
    activa: bool = Field(default=True, description="CATEGORÍA ACTIVA SI/NO")

class Categoria(CategoriaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    productos: List["Producto"] = Relationship(back_populates="categoria")

class ProductoBase(SQLModel): 
    nombre: str = Field(index=True, description="NOMBRE DEL PRODUCTO: ")
    description: Optional[str] = Field(default=None, description="DETALLES DEL PRODUCTO")
    precio: float = Field(gt=0, description="PRECIO DEL PRODUCTO")
    stock: int = Field(ge=0, description="CANTIDAD DISPONIBLE DEL PRODUCTO EN EL INVENTARIO")
    activo: bool = Field(default=True, description="INDICA SI EL PRODUCTO ESTA DISPONIBLE O NO")

class Producto(ProductoBase, table=True): 
    id: Optional[int] = Field(default=None, primary_key=True)
    categoria_id: int = Field(foreign_key="categoria.id", nullable=False)
    categoria: Optional[Categoria] = Relationship(back_populates="productos")