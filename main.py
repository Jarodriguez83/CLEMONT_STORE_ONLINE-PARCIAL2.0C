from contextlib import asynccontextmanager #Sirve para importar un decorador que permite manejar recursos asíncronos (como sesiones o conexiones) dentro de un contexto controlado.
from typing import List, Optional #TIPOS DE DATOS (LIST: Para listas de cierto tipo, OPTIONAL: Para campos opcionales o nulos)

# IMPORTANTE: Importar Depends para la inyección de dependencias
from fastapi import FastAPI, HTTPException, status, Depends #ELEMENTOS PRINCIPALES PARA CREAR UNA API 
    #FASTAPI: INICIALIZAR LA APLICACIÓN, HTTPEXCEPTION: MANEJAR ERRORES HTTP, STATUS: CÓDIGOS DE ESTADO HTTP, DEPENDS: INYECCIÓN DE DEPENDENCIAS
    #HTTPException: permite lanzar errores HTTP personalizados con códigos y mensajes específicos.
    #STATUS: Proporciona constantes legibles para códigos de estado HTTP (como 200, 404, 500).
    #DEPENDS: Permite inyectar dependencias (como sesiones de DB) en las rutas de FastAPI.
from sqlmodel import SQLModel, select, Session #ELEMENTOS NECESARIOS PARA LA BASE DE DATOS
    #SQLMODEL: CLASE BASE PARA MODELOS 
    #SELECT: PARA CONSULTAS A LA BASE DE DATOS
    #SESSION: PARA MANEJAR LAS CONEXIONES CON LA DB

# MANEJO DE ERRORES específicos que pueden OCURRIR en el PROGRAMA
from sqlalchemy.exc import IntegrityError 
    #INTEGRITYERROR: Se usa para capturar errores de la base de datos, por ejemplo, cuando intentas crear una categoría con un nombre duplicado o violas una restricción de clave foránea.
from pydantic import ValidationError
    #VALIDATIONERROR: Se usa para capturar errores de validación de datos generados por Pydantic, por ejemplo, cuando se envían datos con tipos incorrectos o que no cumplen las reglas del modelo.

# Importación de MODELOS y DEPENDENCIAS de la DB
from models import (
    Categoria, CategoriaCreate, CategoriaRead, CategoriaUpdate, CategoriaReadWithProductos,
    Producto, ProductoCreate, ProductoUpdate, ProductoRead, ProductoReadWithCategoria,
    StockUpdate
)
from models import Producto, Comprador, CompradorCreate, CompradorRead, CompraResultado
# 1. MANEJO CON LA BASE DE DATOS
from database import get_session, get_db_engine, create_db_and_tables 
    #get_session: Crea y devuelve una sesión activa para interactuar con la base de datos (leer, crear, actualizar, eliminar).
    #get_db_engine: Obtiene el motor de conexión (engine) que se usa para comunicarse con la base de datos.
    #create_db_and_tables: Crea la base de datos y las tablas si no existen.

engine = get_db_engine() # OBTENER el MOTOR de la BASE DE DATOS

@asynccontextmanager #Sirve para manejar recursos que deben abrirse y cerrarse correctamente
async def lifespan(app: FastAPI): #Función de inicialización y cierre de la aplicación FastAPI
    create_db_and_tables(engine) # Asegura que las tablas se creen
    yield #Pausar su ejecución y devolver temporalmente un valor, pero permitiendo reanudarla más tarde.
    print("CIERRE DE LA APLICACIÓN.")

app = FastAPI(
    title="CLEMONT STORE ONLINE | API",
    version="1.1.0",
    description="API para la gestión de 'CLEMONT STORE ONLINE' con FastAPI y SQLModel. | VISITA NUESTRA WEB OFICIAL: https://clemont.co/",
    lifespan=lifespan, #CONTROLA LAS TAREAS DE INICIO Y DE APAGADO DE LA APLICACIÓN
    docs_url="/docs",
)

@app.get("/")
def read_root():
    return {"message": "CLEMONT STORE ONLINE API. Visita /docs para la documentación y entender el funcionamiento de la API con los ENDPOINTS."}

# 2. ENDPOINTS PARA EL MODELO DE CATEGORÍA
# 2.1. Crear Categoría (POST /categorias/)
@app.post("/categorias/", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
    #POST: Indica que se crea una nueva categoría
    #RESPONSE_MODEL: Define el modelo de respuesta esperado (CategoriaRead) que el cliente recibirá
    #STATUS_CODE: Indica que la respuesta exitosa tendrá el código HTTP 201 (Creado)
def create_categoria(categoria: CategoriaCreate, session: Session = Depends(get_session)):
    #CATEGORIA:CATEGORIACREATE: Datos recibidos para crear la categoría
    #SESSION: Sesión de base de datos inyectada automáticamente por FastAPI usando Depends
    #DEPENDS: Permite inyectar dependencias (como sesiones de DB) en las rutas de FastAPI.
    db_categoria = Categoria.model_validate(categoria) #VALIDAR Y CONVERTIR DATOS DE ENTRADA A MODELO DE BASE DE DATOS
    session.add(db_categoria) #Agrega la nueva categoría a la sesión de la base de datos, pero aún no la guarda definitivamente.
    try: #INICIA BLOQUE DE MANEJO DE ERRORES
        session.commit() #Confirma los cambios realizados en la sesión y los guarda definitivamente en la base de datos.
    except IntegrityError: #IDENTIFICA ERRORES DE INTEGRIDAD DE LA BASE DE DATOS
        session.rollback() # Limpia la transacción fallida
        # Devuelve ERROR 409 Conflict por la regla de unicidad del nombre
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"- YA EXISTE UNA CATEGORIA CON EL NOMBRE '{categoria.nombre}'.",
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

# 2.2. Listar Categorías Activas (GET /categorias/)
@app.get("/categorias/", response_model=List[CategoriaRead])
def read_categorias(session: Session = Depends(get_session)): # Uso de Depends
    categorias = session.exec(select(Categoria).where(Categoria.is_active == True)).all()
    return categorias

# 2.3. Obtener Categoría con Productos (GET /categorias/{id})
@app.get("/categorias/{categoria_id}", response_model=CategoriaReadWithProductos)
def read_categoria_with_productos(categoria_id: int, session: Session = Depends(get_session)): # Uso de Depends
    categoria = session.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Categoría con ID {categoria_id} no encontrada.")
    return categoria

# 2.4. Actualizar Categoría (PATCH /categorias/{id})
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

# 2.5. Eliminar Categoría (DELETE /categorias/{id}) - BAJA LÓGICA EN CASCADA
@app.delete(
    "/categorias/{categoria_id}", 
    status_code=status.HTTP_204_NO_CONTENT # Código estándar para DELETE exitoso sin cuerpo
)
def delete_categoria(categoria_id: int, session: Session = Depends(get_session)):
    """
    Elimina una categoría marcándola como inactiva (is_active = False) 
    y desactiva en cascada todos sus productos activos.
    Responde con 204 No Content.
    """
    db_categoria = session.get(Categoria, categoria_id)
    
    # 1. Verificar si existe (404 Not Found)
    if not db_categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Categoría con ID {categoria_id} no encontrada."
        )

    # 2. Si ya está inactiva, la operación se considera exitosa (Idempotencia)
    if not db_categoria.is_active:
        return 

    # 3. Realizar la Baja Lógica de la Categoría
    db_categoria.is_active = False
    
    # 4. Lógica de Cascada (Desactivar Productos)
    # Selecciona solo los productos que están activos y pertenecen a esta categoría
    productos_a_desactivar = session.exec(
        select(Producto).where(Producto.categoria_id == categoria_id, Producto.is_active == True)
    ).all()
    
    for producto in productos_a_desactivar:
        producto.is_active = False
        session.add(producto) # Agrega cada producto modificado a la sesión

    # 5. Guarda todos los cambios (categoría y productos) en una sola transacción
    session.add(db_categoria)
    session.commit()
    
    # 6. Retorna 204 No Content
    return

# 3. ENDPOINTS para PRODUCTO

# 3.1. Crear Producto (POST /productos/)
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

# 3.2. Listar Productos con Filtros (GET /productos/)
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

# 3.3. Obtener Producto con Categoría (GET /productos/{id})
@app.get("/productos/{producto_id}", response_model=ProductoReadWithCategoria)
def read_producto_with_categoria(producto_id: int, session: Session = Depends(get_session)):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto con ID {producto_id} no encontrado.")
    return producto

# 3.4. Actualizar Producto (PATCH /productos/{id})
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

# 3.5. Eliminar Producto (DELETE /productos/{id}) - BAJA LÓGICA
@app.delete(
    "/productos/{producto_id}", 
    status_code=status.HTTP_204_NO_CONTENT # 204 indica éxito sin cuerpo de respuesta
)
def delete_producto(producto_id: int, session: Session = Depends(get_session)):
    """
    Elimina un producto marcándolo como inactivo (is_active = False).
    Responde con 204 No Content si es exitoso o ya estaba inactivo.
    """
    db_producto = session.get(Producto, producto_id)
    
    # 1. Verificar si existe (404 Not Found)
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Producto con ID {producto_id} no encontrado."
        )
    
    # 2. Si ya está inactivo, podemos devolver 204 igualmente.
    if not db_producto.is_active:
        return 
    
    # 3. Realizar la baja lógica
    db_producto.is_active = False
    
    session.add(db_producto)
    session.commit()
    # No es necesario hacer session.refresh() ni retornar db_producto, 
    # ya que el código 204 no devuelve cuerpo.

# 3.6. Restar Stock / Simular Compra (PATCH /productos/{id}/restar_stock)
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

# 4. Endpoints para COMPRADOR / PROCESO DE VENTA
# 4.1. Registrar Compra (POST /compras/)
@app.post("/compras/", response_model=CompraResultado, status_code=status.HTTP_201_CREATED)
def registrar_compra(comprador_data: CompradorCreate, session: Session = Depends(get_session)):
    """
    Registra una nueva compra, aplicando las reglas de negocio:
    1. Validar edad mínima (Pydantic gestiona el 422).
    2. Validar que el producto exista y esté activo.
    3. Validar stock suficiente.
    4. Aplicar descuento del 20% si se compran 3 o más unidades.
    5. Actualizar el stock del producto.
    """
    
    # 1. Validación: Existencia y Actividad del Producto
    db_producto = session.get(Producto, comprador_data.producto_id)
    
    if not db_producto or not db_producto.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"El producto con ID {comprador_data.producto_id} no existe o no está activo."
        )

    cantidad_a_comprar = comprador_data.cantidad_unidades
    
    # 2. Validación: Stock Suficiente
    if db_producto.stock < cantidad_a_comprar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente para el producto '{db_producto.nombre}'. Stock disponible: {db_producto.stock}.",
        )
        
    # --- LÓGICA DE NEGOCIO Y CÁLCULO ---
    
    # 3. Cálculo de Descuento (Regla: 20% si son 3 o más unidades)
    descuento_porcentaje = 0.0
    if cantidad_a_comprar >= 3:
        descuento_porcentaje = 0.20 # 20% de descuento
    
    precio_unidad = db_producto.precio
    subtotal = precio_unidad * cantidad_a_comprar
    descuento_aplicado = subtotal * descuento_porcentaje
    total_pagar = subtotal - descuento_aplicado
    
    # 4. Creación del registro de Comprador
    db_comprador = Comprador.model_validate(comprador_data)
    
    # 5. Resta de Stock y Guardado
    db_producto.stock -= cantidad_a_comprar
    
    # Iniciar Transacción
    session.add(db_comprador)
    session.add(db_producto)
    
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        # En caso de error de BD inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al procesar la compra: {str(e)}"
        )
        
    session.refresh(db_comprador)
    
    # 6. Preparar Respuesta
    nombre_completo = f"{db_comprador.nombres} {db_comprador.apellidos}"
    
    return CompraResultado(
        mensaje="Compra registrada exitosamente y stock actualizado.",
        nombre_comprador=nombre_completo,
        nombre_producto=db_producto.nombre,
        cantidad_comprada=cantidad_a_comprar,
        precio_unidad=precio_unidad,
        subtotal=round(subtotal, 2),
        descuento_aplicado=round(descuento_aplicado, 2),
        total_pagar=round(total_pagar, 2)
    )

# 4.2. Listar Compras (GET /compras/)
@app.get("/compras/", response_model=List[CompradorRead])
def read_compras(session: Session = Depends(get_session)):
    """
    Lista todos los registros de compra.
    """
    compras = session.exec(select(Comprador)).all()
    return compras