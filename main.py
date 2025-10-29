# CLEMONT_STORE_ONLINE/main.py

from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from sqlmodel import create_engine, SQLModel, Session, select
from pydantic import ValidationError

from models import (
    # Clases de Categoría (ya estaban)
    Categoria, CategoriaCreate, CategoriaRead, CategoriaUpdate,
    CategoriaReadWithProductos,
    
    # Clases de Producto y Stock (las que faltaban)
    Producto, ProductoCreate, ProductoUpdate,
    ProductoRead, ProductoReadWithCategoria, # Incluyendo la de lectura con relación
    StockUpdate # El modelo para restar stock
)

# ----------------------------------------------------------------------
# 1. Configuración de la Base de Datos (SQLite)
# ----------------------------------------------------------------------

# Se recomienda usar variables de entorno para esto, pero por simplicidad
# y para mantener la base de datos en el mismo directorio, lo definimos aquí.
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# El parámetro connect_args={"check_same_thread": False} es necesario para SQLite
# cuando se usa en un entorno asíncrono como FastAPI.
engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """
    Crea las tablas en la base de datos si no existen, usando los modelos SQLModel.
    """
    SQLModel.metadata.create_all(engine)
    print("Base de datos y tablas creadas exitosamente.")

# ----------------------------------------------------------------------
# 2. Contexto de Vida de la Aplicación (FastAPI)
# ----------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Función que se ejecuta al inicio y al final de la vida de la app.
    Usada para inicializar la DB.
    """
    # Ejecución al inicio (Startup)
    create_db_and_tables()
    yield
    # Ejecución al cierre (Shutdown)
    print("Aplicación cerrada.")

# Inicialización de la aplicación FastAPI con el contexto de vida (lifespan)
app = FastAPI(
    title="CLEMONT Store Online API (Sistema de Gestión)",
    description="API REST para la gestión de productos, categorías y stock de la tienda de ropa Clemont.",
    version="1.0.0",
    docs_url="/docs",  # Asegura que el Swagger esté en /docs
    redoc_url=None
)

# ----------------------------------------------------------------------
# 3. Función de Utilidad (Obtener Sesión de DB)
# ----------------------------------------------------------------------

def get_session():
    """
    Generador para obtener una nueva sesión de base de datos.
    Usado como dependencia en los endpoints.
    """
    with Session(engine) as session:
        yield session

# ----------------------------------------------------------------------
# 4. Endpoints para CATEGORÍA (CRUD Básico + Lógica de Negocio)
# ----------------------------------------------------------------------

# A. Crear Categoría (POST /categorias/)
@app.post("/categorias/", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def create_categoria(categoria: CategoriaCreate, session: Session = next(get_session())):
    """
    Registra una nueva categoría.
    
    Lógica de Negocio:
    - Nombre de categoría único (409 Conflict si ya existe).
    """
    # Verificar unicidad del nombre antes de intentar crear
    existing_category = session.exec(
        select(Categoria).where(Categoria.nombre == categoria.nombre)
    ).first()
    
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una categoría con el nombre '{categoria.nombre}'."
        )

    db_categoria = Categoria.model_validate(categoria)
    
    session.add(db_categoria)
    session.commit()
    session.refresh(db_categoria)
    return db_categoria

# B. Listar Categorías Activas (GET /categorias/)
@app.get("/categorias/", response_model=List[CategoriaRead])
def read_categorias(session: Session = next(get_session())):
    """
    Lista todas las categorías activas (is_active = True).
    """
    # Cumple con el requisito: Listar categorías (solo las activas)
    categorias = session.exec(select(Categoria).where(Categoria.is_active == True)).all()
    return categorias

# C. Obtener Categoría con Productos (GET /categorias/{id})
@app.get("/categorias/{categoria_id}", response_model=CategoriaReadWithProductos)
def read_categoria_with_productos(categoria_id: int, session: Session = next(get_session())):
    """
    Obtiene una categoría por su ID, incluyendo la lista de sus productos.
    (Cumple con el requisito: Obtener categoría y sus productos)
    """
    # SQLModel automáticamente carga los productos relacionados al usar el esquema CategoriaReadWithProductos
    categoria = session.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {categoria_id} no encontrada."
        )
    return categoria

# D. Actualizar Categoría (PATCH /categorias/{id})
@app.patch("/categorias/{categoria_id}", response_model=CategoriaRead)
def update_categoria(categoria_id: int, categoria: CategoriaUpdate, session: Session = next(get_session())):
    """
    Actualiza parcialmente los datos de una categoría.
    Maneja la Regla de Negocio: Nombre de categoría único.
    """
    db_categoria = session.get(Categoria, categoria_id)
    if not db_categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {categoria_id} no encontrada."
        )

    # Verificar unicidad del nuevo nombre, si se está actualizando
    if categoria.nombre and categoria.nombre != db_categoria.nombre:
        existing_category = session.exec(
            select(Categoria).where(Categoria.nombre == categoria.nombre)
        ).first()
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe otra categoría con el nombre '{categoria.nombre}'."
            )

    # Aplicar la actualización
    categoria_data = categoria.model_dump(exclude_unset=True)
    for key, value in categoria_data.items():
        setattr(db_categoria, key, value)

    session.add(db_categoria)
    session.commit()
    session.refresh(db_categoria)
    return db_categoria

# E. Desactivar Categoría (PATCH /categorias/{id}/desactivar)
@app.patch("/categorias/{categoria_id}/desactivar", response_model=CategoriaRead)
def deactivate_categoria(categoria_id: int, session: Session = next(get_session())):
    """
    Desactiva una categoría (is_active = False) y, por la regla de negocio
    de cascada, desactiva sus productos asociados.
    (Cumple con el requisito: Desactivar categoría y la lógica de cascada)
    """
    db_categoria = session.get(Categoria, categoria_id)
    if not db_categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {categoria_id} no encontrada."
        )

    if not db_categoria.is_active:
        return db_categoria # Ya está inactiva, retorna el estado actual

    # 1. Desactivar la categoría
    db_categoria.is_active = False
    
    # 2. Aplicar la Lógica de Negocio de Cascada: Desactivar productos asociados
    # Cargamos los productos a través de la relación para modificar su estado
    
    # Nota: Si se usan operaciones de cascada directas de SQLAlchemy, esto podría ser
    # automático, pero es mejor implementarlo explícitamente aquí para control.
    
    productos_a_desactivar = session.exec(
        select(Producto).where(Producto.categoria_id == categoria_id)
    ).all()
    
    productos_desactivados_count = 0
    for producto in productos_a_desactivar:
        if producto.is_active:
            producto.is_active = False
            session.add(producto)
            productos_desactivados_count += 1

    session.add(db_categoria)
    session.commit()
    session.refresh(db_categoria)
    
    print(f"INFO: Se desactivaron {productos_desactivados_count} productos en cascada para la Categoría ID {categoria_id}.")
    
    return db_categoria

# F. Endpoint de Prueba (Raíz)
@app.get("/")
def read_root():
    return {"message": "CLEMONT Store Online API está operativa."}

# ----------------------------------------------------------------------
# 5. Manejo de Errores Adicionales (Ejemplo)
# ----------------------------------------------------------------------

# (Opcional, pero útil) Se podría añadir un manejo de excepciones global para
# errores de validación de Pydantic o errores de DB más específicos.
# A. Crear Producto (POST /productos/)
@app.post("/productos/", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def create_producto(producto: ProductoCreate, session: Session = next(get_session())):
    """
    Registra un nuevo producto.

    Lógica de Negocio:
    - Todos los productos deben tener una categoría existente (400 Bad Request).
    - Stock inicial >= 0 (Validado por Pydantic/SQLModel).
    """
    # 1. Verificar si la categoría existe (Regla de Negocio: Categoría Obligatoria)
    categoria = session.get(Categoria, producto.categoria_id)
    if not categoria or not categoria.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La categoría con ID {producto.categoria_id} no existe o está inactiva. No se puede crear el producto."
        )

    db_producto = Producto.model_validate(producto)
    
    session.add(db_producto)
    session.commit()
    session.refresh(db_producto)
    return db_producto

# B. Listar Productos con Filtros (GET /productos/)
@app.get("/productos/", response_model=List[ProductoReadWithCategoria])
def read_productos(
    stock: Optional[int] = None, 
    precio_min: Optional[float] = None, # Filtro 1
    precio_max: Optional[float] = None, # Filtro 2 (Cumple con los 2+ parámetros requeridos)
    categoria_id: Optional[int] = None,
    session: Session = next(get_session())
):
    """
    Lista productos activos. Permite filtrar por stock (igual o mayor), rango de precio y categoría.
    """
    # Consulta base: solo productos activos
    query = select(Producto).where(Producto.is_active == True)
    
    if stock is not None:
        # Filtra productos con stock mayor o igual al valor dado
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
def read_producto_with_categoria(producto_id: int, session: Session = next(get_session())):
    """
    Obtiene un producto por su ID, incluyendo los datos de la categoría a la que pertenece.
    (Cumple con el requisito: Obtener producto con categoría)
    """
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado."
        )
    return producto

# D. Actualizar Producto (PATCH /productos/{id})
@app.patch("/productos/{producto_id}", response_model=ProductoRead)
def update_producto(producto_id: int, producto: ProductoUpdate, session: Session = next(get_session())):
    """
    Actualiza parcialmente los datos de un producto.
    
    Validaciones:
    - Stock no puede ser negativo (Validado por Pydantic en ProductoUpdate).
    - Si se cambia categoria_id, la nueva categoría debe existir y estar activa.
    """
    db_producto = session.get(Producto, producto_id)
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado."
        )

    # 1. Verificar nueva categoría si se proporciona
    if producto.categoria_id is not None and producto.categoria_id != db_producto.categoria_id:
        categoria = session.get(Categoria, producto.categoria_id)
        if not categoria or not categoria.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La nueva categoría con ID {producto.categoria_id} no existe o está inactiva."
            )

    # 2. Aplicar la actualización
    # Esto también manejará la validación del stock (>= 0) debido a la herencia de SQLModel/Pydantic
    try:
        producto_data = producto.model_dump(exclude_unset=True)
        for key, value in producto_data.items():
            setattr(db_producto, key, value)
    except ValidationError as e:
        # Captura errores de Pydantic, como si se intenta establecer stock < 0
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.errors())

    session.add(db_producto)
    session.commit()
    session.refresh(db_producto)
    return db_producto

# E. Desactivar Producto (PATCH /productos/{id}/desactivar)
@app.patch("/productos/{producto_id}/desactivar", response_model=ProductoRead)
def deactivate_producto(producto_id: int, session: Session = next(get_session())):
    """
    Marca un producto como inactivo (is_active = False).
    """
    db_producto = session.get(Producto, producto_id)
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado."
        )
    
    if not db_producto.is_active:
        return db_producto # Ya está inactivo

    db_producto.is_active = False
    
    session.add(db_producto)
    session.commit()
    session.refresh(db_producto)
    return db_producto

# F. Restar Stock / Simular Compra (PATCH /productos/{id}/restar_stock)
@app.patch("/productos/{producto_id}/restar_stock", response_model=ProductoRead)
def restar_stock(producto_id: int, stock_update: StockUpdate, session: Session = next(get_session())):
    """
    Resta una cantidad específica del stock del producto (Simula una venta/compra).

    Lógica de Negocio:
    - Stock no puede ser negativo (400 Bad Request si el stock es insuficiente).
    - Comprar un producto modifica las cantidades del stock.
    """
    db_producto = session.get(Producto, producto_id)
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado."
        )

    cantidad_a_restar = stock_update.cantidad_a_restar
    
    # 1. Aplicar la Regla de Negocio: Stock no puede ser negativo
    if db_producto.stock < cantidad_a_restar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Stock actual: {db_producto.stock}. La cantidad a restar ({cantidad_a_restar}) excede el stock disponible."
        )
        
    # 2. Modificar el stock
    db_producto.stock -= cantidad_a_restar
    
    session.add(db_producto)
    session.commit()
    session.refresh(db_producto)
    
    return db_producto

# ----------------------------------------------------------------------
# (Fin de la implementación de Endpoints)
# ----------------------------------------------------------------------