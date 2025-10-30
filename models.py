from typing import List, Optional #TIPOS DE DATOS (LIST: Para listas de cierto tipo, OPTIONAL: Para campos opcionales o nulos)
from sqlmodel import Field, SQLModel, Relationship #SQLMODEL (Field: Para definir campos de la tabla, SQLModel: Clase base para modelos, Relationship: Para relaciones entre tablas)
from pydantic import EmailStr, PositiveFloat, validator, conint, conlist ##VALIDADORES DE Pydantic (EmailStr: Valida formato de correo, PositiveFloat: Valida float positivo, validator: Crea validadores personalizados, conint: Enteros con restricciones, conlist: Listas con restricciones)

#  MODELO DE CATEGORÍA (1:N) 
class CategoriaBase(SQLModel): #PARA DEFINIR CAMPOS 
    nombre: str = Field(index=True, unique=True, min_length=3, max_length=50)
    #FIELD para agregar RESTRICCIONES (index: Crea índice para búsquedas rápidas, unique: Evita duplicados, min_length/max_length: Longitud del string)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    #La DESCRIPCIÓN es OPCIONAL (puede ser nula), con LONGITUD MÁXIMA de 255 caracteres y default None para que sea nula si no se proporciona
    is_active: bool = Field(default=True)
    #INDICA si la categoría está ACTIVA (por defecto es True)

class Categoria(CategoriaBase, table=True, unique=True): #PARA CREAR LA TABLA POR MEDIO DE LA CLASE DEFINIDA
    id: Optional[int] = Field(default=None, primary_key=True)
    #El ID es la CLAVE PRIMARIA (primary_key=True) y es OPCIONAL (es autoincremental)
    productos: List["Producto"] = Relationship(back_populates="categoria")
    #RELACIÓN UNO A MUCHOS (1:N) con Producto (una categoría tiene muchos productos)
    #RELACIONSHIP para conectar ambos modelos y back_populates para enlazar con el campo correspondiente en el otro modelo

class CategoriaCreate(CategoriaBase):
    #POST para la creación de una nueva categoría
    pass

class CategoriaUpdate(SQLModel):
    #PATCH para la actualización parcial de una categoría
    nombre: Optional[str] = Field(default=None, index=True, unique=True, min_length=3, max_length=50)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = Field(default=None)

# MODELO DE PRODUCTO (1:N) 
class ProductoBase(SQLModel): #PARA DEFINIR CAMPOS
    nombre: str = Field(min_length=3, max_length=100, unique=True) # Nombre del producto con restricciones de longitud en el 'string'
    precio: PositiveFloat  # Asegura que el precio sea positivo (> 0)
    stock: conint(ge=0) = Field(ge=0) # type: ignore # Stock debe ser mayor o igual a cero
    descripcion: Optional[str] = Field(default=None, max_length=500) # Descripción opcional con longitud máxima de 500 caracteres
    is_active: bool = Field(default=True) # Indica si el producto está activo (por defecto es True)
    # Clave Foránea (FK)
    categoria_id: int = Field(foreign_key="categoria.id", index=True)

class Producto(ProductoBase, table=True): #PARA CREAR LA TABLA POR MEDIO DE LA CLASE DEFINIDA
    id: Optional[int] = Field(default=None, primary_key=True) # El ID es la CLAVE PRIMARIA (primary_key=True) y es OPCIONAL (es autoincremental)
    categoria: "Categoria" = Relationship(back_populates="productos") # RELACIÓN MUCHOS A UNO (N:1) con Categoría

class ProductoCreate(ProductoBase):
    #POST para la creación de un nuevo producto
    pass

class ProductoUpdate(SQLModel):
    #PATCH para la actualización parcial de un producto
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    precio: Optional[PositiveFloat] = Field(default=None)
    stock: Optional[conint(ge=0)] = Field(default=None, ge=0) # type: ignore
    descripcion: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)
    categoria_id: Optional[int] = Field(default=None, foreign_key="categoria.id", index=True)

#  Esquemas para Lectura/Respuesta (Evita Recursión) 
class StockUpdate(SQLModel):
    #ENDPOINT para actualizar el stock del producto (restar cantidad)
    cantidad_a_restar: conint(gt=0) # type: ignore #CONINT para asegurar que la cantidad a restar sea mayor a 0

class CategoriaReadOnly(CategoriaBase):
    #UTILIZADO PARA MOTRAR INFORMACIÓN (NO MODIFICAR)
    id: int

class ProductoRead(ProductoBase):
    #PRODUCTO para ser listado.
    id: int

class ProductoReadWithCategoria(ProductoRead):
    #INCLUIR INFORMACIÓN DE LA CATEGORÍA
    categoria: CategoriaReadOnly

class CategoriaRead(CategoriaBase):
    #CATEGORIA para ser LISTADO SIN PRODUCTOS.
    id: int

class CategoriaReadWithProductos(CategoriaRead):
    #ESQUEMA QUE INCLUYE LISTA DE PRODUCTOS
    productos: List[ProductoRead] = []

# Se usa cuando dos clases se hacen referencia mutuamente, y una de ellas todavía no está definida en el momento en que la otra la menciona.
Producto.update_forward_refs()
Categoria.update_forward_refs()

class CompradorBase(SQLModel): #DEFINICIÓN DE CAMPOS PARA COMPRADOR Y DETALLE DE COMPRA
    nombres: str = Field(min_length=2, max_length=50)
    apellidos: str = Field(min_length=2, max_length=50)
    # Importante RESTRICCIÓN: Edad debe ser mayor o igual a 18
    edad: conint(ge=18) = Field(ge=18)  # type: ignore
    correo_electronico: EmailStr = Field(index=True) #EmailStr para validar formato de correo y que sea único
    medio_pago: str = Field(min_length=3, max_length=50)
    producto_id: int = Field(foreign_key="producto.id", index=True) # Clave foránea al producto (ID para reconocer el producto)
    cantidad_unidades: conint(ge=1) = Field(ge=1)  # type: ignore # RESTRICCIÓN: Cantidad debe ser mayor o igual a 1

class Comprador(CompradorBase, table=True):
    #MODELO DE LA TABLA COMPRADOR
    id: Optional[int] = Field(default=None, primary_key=True)

class CompradorCreate(CompradorBase):
    # Registro de compra (POST).
    pass

class CompradorRead(CompradorBase):
    #COMPRADOR para ser listado.
    id: int

class CompraResultado(SQLModel):
    #MUESTRA los atributos que va a devolver al realizar una compra
    mensaje: str
    nombre_comprador: str
    nombre_producto: str
    cantidad_comprada: int
    precio_unidad: float
    subtotal: float
    descuento_aplicado: float
    total_pagar: float