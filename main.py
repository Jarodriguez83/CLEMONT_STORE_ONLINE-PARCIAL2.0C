# CLEMONT_STORE_ONLINE/main.py

from contextlib import asynccontextmanager
from typing import List, Optional

# Corrección CRÍTICA: Importar Depends para la inyección de dependencias
from fastapi import FastAPI, HTTPException, status, Depends
from sqlmodel import SQLModel, select, Session
# Corrección CRÍTICA: Importar el error específico de la DB
from sqlalchemy.exc import IntegrityError 
from pydantic import ValidationError

# Importación de modelos y dependencias de la DB
from models import (
    Categoria, CategoriaCreate, CategoriaRead, CategoriaUpdate, CategoriaReadWithProductos,
    Producto, ProductoCreate, ProductoUpdate, ProductoRead, ProductoReadWithCategoria,
    StockUpdate
)
from database import get_session, get_db_engine, create_db_and_tables 

# ----------------------------------------------------------------------
# 1. Configuración de la Aplicación y la Base de Datos
# ----------------------------------------------------------------------

# Obtener el motor de la DB para el contexto de vida
engine = get_db_engine() 

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Función que se ejecuta al inicio de la app para inicializar la DB.
    """
    create_db_and_tables(engine) # Asegura que las tablas se creen
    yield
    print("Aplicación cerrada.")

app = FastAPI(
    title="CLEMONT Store Online API",
    version="1.0.0",
    lifespan=lifespan, # CRÍTICO: Vincula la función de inicialización
    docs_url="/docs",
)

@app.get("/")
def read_root():
    return {"message": "CLEMONT Store Online API está operativa. Visita /docs para la documentación."}

# ----------------------------------------------------------------------
# 2. Endpoints para CATEGORÍA
# ----------------------------------------------------------------------

# A. Crear Categoría (POST /categorias/)
@app.post("/categorias/", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
# Corrección CRÍTICA: Uso de Depends(get_session)
def create_categoria(categoria: CategoriaCreate, session: Session = Depends(get_session)):
    db_categoria = Categoria.model_validate(categoria)
    session.add(db_categoria)
    
    try:
        session.commit() # Intenta guardar
    except IntegrityError:
        session.rollback() # Limpia la transacción fallida
        # Devuelve 409 Conflict por la regla de unicidad del nombre
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una categoría con el nombre '{categoria.nombre}'.",
        )
    except Exception as e:
        session.rollback()
        # Devuelve 500 para cualquier otro error de DB
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al guardar en la base de datos: {str(e)}",
        )
        
    session.refresh(db_categoria)
    return db_categoria

# B. Listar Categorías Activas (GET /categorias/)
@app.get("/categorias/", response_model=List[CategoriaRead])
def read_categorias(session: Session = Depends(get_session)): # Uso de Depends
    categorias = session.exec(select(Categoria).where(Categoria.is_active == True)).all()
    return categorias

# C. Obtener Categoría con Productos (GET /categorias/{id})
@app.get("/categorias/{categoria_id}", response_model=CategoriaReadWithProductos)
def read_categoria_with_productos(categoria_id: int, session: Session = Depends(get_session)): # Uso de Depends
    categoria = session.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Categoría con ID {categoria_id} no encontrada.")
    return categoria

# D. Actualizar Categoría (PATCH /categorias/{id})
@app.patch("/categorias/{categoria_id}", response_model=CategoriaRead)
def update_categoria(categoria_id: int, categoria: CategoriaUpdate, session: Session = Depends(get_session)):
    db_categoria = session.get(Categoria, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Categoría con ID {categoria_id} no encontrada.")

    # Verificar unicidad del nuevo nombre
    if categoria.nombre and categoria.nombre != db_categoria.nombre:
        existing_category = session.exec(select(Categoria).where(Categoria.nombre == categoria.nombre)).first()
        if existing_category:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe otra categoría con el nombre '{categoria.nombre}'.")

    categoria_data = categoria.model_dump(exclude_unset=True)
    for key, value in categoria_data.items():
        setattr(db_categoria, key, value)

    session.add(db_categoria)
    session.commit()
    session.refresh(db_categoria)
    return db_categoria

# E. Desactivar Categoría (PATCH /categorias/{id}/desactivar)
@app.patch("/categorias/{categoria_id}/desactivar", response_model=CategoriaRead)
def deactivate_categoria(categoria_id: int, session: Session = Depends(get_session)):
    db_categoria = session.get(Categoria, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Categoría con ID {categoria_id} no encontrada.")

    if not db_categoria.is_active:
        return db_categoria 

    db_categoria.is_active = False
    
    # Lógica de Cascada
    productos_a_desactivar = session.exec(
        select(Producto).where(Producto.categoria_id == categoria_id, Producto.is_active == True)
    ).all()
    
    for producto in productos_a_desactivar:
        producto.is_active = False
        session.add(producto)

    session.add(db_categoria)
    session.commit()
    session.refresh(db_categoria)
    return db_categoria

# ----------------------------------------------------------------------
# 3. Endpoints para PRODUCTO
# ----------------------------------------------------------------------

# A. Crear Producto (POST /productos/)
@app.post("/productos/", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def create_producto(producto: ProductoCreate, session: Session = Depends(get_session)):
    categoria = session.get(Categoria, producto.categoria_id)
    if not categoria or not categoria.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La categoría con ID {producto.categoria_id} no existe o está inactiva. No se puede crear el producto."
        )

    db_producto = Producto.model_validate(producto)
    session.add(db_producto)
    
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado al guardar el producto: {str(e)}")
        
    session.refresh(db_producto)
    return db_producto

# B. Listar Productos con Filtros (GET /productos/)
@app.get("/productos/", response_model=List[ProductoReadWithCategoria])
def read_productos(
    stock: Optional[int] = None, 
    precio_min: Optional[float] = None, 
    precio_max: Optional[float] = None, 
    categoria_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    query = select(Producto).where(Producto.is_active == True)
    
    if stock is not None:
        query = query.where(Producto.stock >= stock) 
    if precio_min is not None:
        query = query.where(Producto.precio >= precio_min)
    if precio_max is not None:
        query = query.where(Producto.precio <= precio_max)
    if categoria_id is not None:
        query = query.where(Producto.categoria_id == categoria_id)

    productos = session.exec(query).all()
    return productos

# C. Obtener Producto con Categoría (GET /productos/{id})
@app.get("/productos/{producto_id}", response_model=ProductoReadWithCategoria)
def read_producto_with_categoria(producto_id: int, session: Session = Depends(get_session)):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto con ID {producto_id} no encontrado.")
    return producto

# D. Actualizar Producto (PATCH /productos/{id})
@app.patch("/productos/{producto_id}", response_model=ProductoRead)
def update_producto(producto_id: int, producto: ProductoUpdate, session: Session = Depends(get_session)):
    db_producto = session.get(Producto, producto_id)
    if not db_producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto con ID {producto_id} no encontrado.")

    # 1. Verificar nueva categoría si se proporciona
    if producto.categoria_id is not None and producto.categoria_id != db_producto.categoria_id:
        categoria = session.get(Categoria, producto.categoria_id)
        if not categoria or not categoria.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La nueva categoría con ID {producto.categoria_id} no existe o está inactiva."
            )

    # 2. Aplicar la actualización, capturando errores de Pydantic (stock < 0)
    try:
        producto_data = producto.model_dump(exclude_unset=True)
        for key, value in producto_data.items():
            setattr(db_producto, key, value)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.errors())

    session.add(db_producto)
    session.commit()
    session.refresh(db_producto)
    return db_producto

# E. Desactivar Producto (PATCH /productos/{id}/desactivar)
@app.patch("/productos/{producto_id}/set-inactive", response_model=ProductoRead) 
def deactivate_producto(producto_id: int, session: Session = Depends(get_session)):
    """
    Marca un producto como inactivo (is_active = False).
    """
    db_producto = session.get(Producto, producto_id)
    if not db_producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto con ID {producto_id} no encontrado.")
    
    if not db_producto.is_active:
        return db_producto 

    db_producto.is_active = False
    session.add(db_producto)
    session.commit()
    session.refresh(db_producto)
    return db_producto

# F. Restar Stock / Simular Compra (PATCH /productos/{id}/restar_stock)
@app.patch("/productos/{producto_id}/restar_stock", response_model=ProductoRead)
def restar_stock(producto_id: int, stock_update: StockUpdate, session: Session = Depends(get_session)):
    db_producto = session.get(Producto, producto_id)
    if not db_producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto con ID {producto_id} no encontrado.")

    cantidad_a_restar = stock_update.cantidad_a_restar
    
    # Regla de Negocio: Stock no puede ser negativo
    if db_producto.stock < cantidad_a_restar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Stock actual: {db_producto.stock}. La cantidad a restar ({cantidad_a_restar}) excede el stock disponible."
        )
        
    db_producto.stock -= cantidad_a_restar
    
    session.add(db_producto)
    session.commit()
    session.refresh(db_producto)
    
    return db_producto