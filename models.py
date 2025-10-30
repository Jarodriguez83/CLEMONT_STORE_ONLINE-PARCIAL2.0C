# CLEMONT_STORE_ONLINE/models.py

from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship
from pydantic import PositiveFloat, validator, conint, conlist

# --- BASE DE DATOS Y ESQUEMAS ---

# --- Modelo CATEGORÍA (Padre - '1' en 1:N) ---

class CategoriaBase(SQLModel):
    """ Define los campos comunes. """
    nombre: str = Field(index=True, unique=True, min_length=3, max_length=50)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)

class Categoria(CategoriaBase, table=True):
    """ Modelo de la tabla 'categoria'. """
    id: Optional[int] = Field(default=None, primary_key=True)
    productos: List["Producto"] = Relationship(back_populates="categoria")

class CategoriaCreate(CategoriaBase):
    """ Esquema para la creación (POST). """
    pass

class CategoriaUpdate(SQLModel):
    """ Esquema para la actualización parcial (PATCH). """
    nombre: Optional[str] = Field(default=None, index=True, unique=True, min_length=3, max_length=50)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = Field(default=None)


# --- Modelo PRODUCTO (Hijo - 'N' en 1:N) ---

class ProductoBase(SQLModel):
    """ Define los campos comunes. """
    nombre: str = Field(min_length=3, max_length=100)
    precio: PositiveFloat  # Asegura que el precio sea positivo (> 0)
    stock: conint(ge=0) = Field(ge=0) # type: ignore # Stock debe ser mayor o igual a cero
    descripcion: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    
    # Clave Foránea (FK)
    categoria_id: int = Field(foreign_key="categoria.id", index=True)

class Producto(ProductoBase, table=True):
    """ Modelo de la tabla 'producto'. """
    id: Optional[int] = Field(default=None, primary_key=True)
    categoria: "Categoria" = Relationship(back_populates="productos")

class ProductoCreate(ProductoBase):
    """ Esquema para la creación (POST). """
    pass

class ProductoUpdate(SQLModel):
    """ Esquema para la actualización parcial (PATCH). """
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    precio: Optional[PositiveFloat] = Field(default=None)
    stock: Optional[conint(ge=0)] = Field(default=None, ge=0) # type: ignore
    descripcion: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)
    categoria_id: Optional[int] = Field(default=None, foreign_key="categoria.id", index=True)


# --- Esquemas para Lectura/Respuesta (Evita Recursión) ---

class StockUpdate(SQLModel):
    """ Esquema para el endpoint PATCH /restar_stock. """
    cantidad_a_restar: conint(gt=0) # type: ignore # Cantidad debe ser mayor a cero

class CategoriaReadOnly(CategoriaBase):
    """ Versión simple de Categoría para incluir en ProductoRead. """
    id: int

class ProductoRead(ProductoBase):
    """ Versión de Producto para ser listado. """
    id: int

class ProductoReadWithCategoria(ProductoRead):
    """ Esquema que incluye la información de la categoría. """
    categoria: CategoriaReadOnly

class CategoriaRead(CategoriaBase):
    """ Esquema de Categoría para ser listado sin productos. """
    id: int

class CategoriaReadWithProductos(CategoriaRead):
    """ Esquema que incluye la lista de sus Productos. """
    productos: List[ProductoRead] = []

# Resolver la dependencia circular de las relaciones bidireccionales
Producto.update_forward_refs()
Categoria.update_forward_refs()