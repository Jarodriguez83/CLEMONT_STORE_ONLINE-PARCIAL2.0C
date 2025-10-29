# CLEMONT_STORE_ONLINE/models.py

from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship
from pydantic import PositiveFloat, validator

# ----------------------------------------------------------------------
# 1. Base de Datos (SQLModel - Base y Modelos Pydantic)
# ----------------------------------------------------------------------

# Esquema Base para respuestas y actualizaciones
# Nota: La herencia de SQLModel garantiza compatibilidad con Pydantic.

# --- Modelo CATEGORÍA (Padre - '1' en 1:N) ---

class CategoriaBase(SQLModel):
    """
    Define los campos comunes para crear, actualizar y listar categorías.
    """
    nombre: str = Field(index=True, unique=True, min_length=3, max_length=50)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)

class Categoria(CategoriaBase, table=True):
    """
    Modelo de la tabla 'categoria' en la base de datos (SQLModel Table).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relación a Productos (productos es la 'List' del lado 'N')
    # back_populates enlaza con el campo 'categoria' del modelo Producto.
    productos: List["Producto"] = Relationship(back_populates="categoria")

class CategoriaCreate(CategoriaBase):
    """
    Esquema Pydantic para la creación de categorías (POST).
    """
    # Sobreescribe para hacer que 'is_active' no sea necesario en la creación
    is_active: bool = Field(default=True)

class CategoriaUpdate(SQLModel):
    """
    Esquema Pydantic para la actualización (PATCH/PUT), todos los campos son opcionales.
    """
    nombre: Optional[str] = Field(default=None, index=True, unique=True, min_length=3, max_length=50)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = Field(default=None)

# --- Modelo PRODUCTO (Hijo - 'N' en 1:N) ---

class ProductoBase(SQLModel):
    """
    Define los campos comunes para crear, actualizar y listar productos.
    """
    nombre: str = Field(min_length=3, max_length=100)
    precio: PositiveFloat
    stock: int = Field(ge=0) # ge=0: Stock debe ser mayor o igual a cero (Regla de Negocio: no negativo)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    
    # Clave Foránea (FK) para la relación 1:N
    categoria_id: int = Field(foreign_key="categoria.id", index=True)

class Producto(ProductoBase, table=True):
    """
    Modelo de la tabla 'producto' en la base de datos (SQLModel Table).
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    # Relación a Categoría (campo 'categoria' es el lado '1' de la relación)
    categoria: Categoria = Relationship(back_populates="productos")
    
    @validator('stock')
    def stock_must_be_non_negative(cls, value):
        """
        Validación adicional de Pydantic para asegurar que el stock no sea negativo.
        Se usa en la creación y actualización.
        """
        if value < 0:
            raise ValueError("El stock no puede ser negativo.")
        return value

class ProductoCreate(ProductoBase):
    """
    Esquema Pydantic para la creación de productos (POST).
    """
    pass # Hereda todas las validaciones de ProductoBase (incluyendo stock >= 0)

class ProductoUpdate(SQLModel):
    """
    Esquema Pydantic para la actualización (PATCH/PUT).
    """
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    precio: Optional[PositiveFloat] = Field(default=None)
    stock: Optional[int] = Field(default=None, ge=0)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)
    categoria_id: Optional[int] = Field(default=None, foreign_key="categoria.id", index=True)


# ----------------------------------------------------------------------
# 2. Esquemas de Lectura/Respuesta (Con relaciones)
# ----------------------------------------------------------------------

# Usaremos esquemas Pydantic específicos para las respuestas JSON que incluyen
# la información relacionada, evitando bucles de referencia circulares.

# --- Esquemas de Lectura para Categoría ---

class ProductoRead(ProductoBase):
    """
    Esquema de Producto para ser incluido dentro de CategoriaRead.
    No incluye la relación de vuelta a Categoría.
    """
    id: int

class CategoriaRead(CategoriaBase):
    """
    Esquema de respuesta para una Categoría (GET by ID o GET all).
    """
    id: int

# --- Esquemas de Lectura para Producto ---

class CategoriaReadOnly(CategoriaBase):
    """
    Esquema de Categoría para ser incluido dentro de ProductoReadWithCategoria.
    Solo incluye los datos básicos, sin la lista de productos.
    """
    id: int

class ProductoReadWithCategoria(ProductoRead):
    """
    Esquema de respuesta para un Producto, incluyendo los datos de su Categoría.
    (Cumple con 'Obtener producto con categoría')
    """
    categoria: CategoriaReadOnly

class CategoriaReadWithProductos(CategoriaRead):
    """
    Esquema de respuesta para una Categoría, incluyendo la lista de sus Productos.
    (Cumple con 'Obtener categoría y sus productos')
    """
    productos: List[ProductoRead] = []

# Nota: Se añade importaciones al final para resolver la dependencia circular
# entre Categoria y Producto para las relaciones.
# En SQLModel esto se maneja con strings o con la importación tardía.
# Aquí lo hacemos de forma explícita para claridad.

Producto.update_forward_refs()
Categoria.update_forward_refs()

# ----------------------------------------------------------------------
# Lógica Adicional (Para Restar Stock)
# ----------------------------------------------------------------------

class StockUpdate(SQLModel):
    """
    Esquema Pydantic para el endpoint PATCH /productos/{id}/restar_stock.
    Solo necesita la cantidad a restar.
    """
    cantidad_a_restar: int = Field(gt=0) # gt=0: La cantidad a restar debe ser positiva