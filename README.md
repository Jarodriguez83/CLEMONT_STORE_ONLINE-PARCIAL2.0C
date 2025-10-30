# CLEMONT_STORE_ONLINE-PARCIAL2.0C
'CLEMONT STORE' es una aplicación de API REST, la cual está integrada con FastAPI, SQLModel, SQLite, entre otros. La cual permite tener un modelo de negocio de 'Tienda Online' para el 'Sistema de Gestión' en donde también existen relaciones 1:N, N:1. Y manejo de excepciones HTTP. Funcionamiento con 'Endpoints' que responden en formato JSON.
CLEMONT Store Online API

API de gestión de un sistema de comercio electrónico (e-commerce) simple para la administración de categorías, productos, inventario y registro de ventas. Desarrollada con FastAPI y SQLModel (SQLAlchemy).

1. Configuración e Instalación

1.1 Requisitos Previos

Asegúrate de tener Python instalado.

1.2 Instalación de Dependencias

Se recomienda usar un entorno virtual (venv).

# Crear entorno virtual (si no existe)
python -m venv venv

# Activar entorno virtual
# En Windows:
.\venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar los requerimientos necesarios.
pip install -r requirements.txt

1.3 Ejecución del Servidor

Una vez activado el entorno, inicia la aplicación usando Uvicorn.

fastapi dev

El servidor estará disponible en: http://127.0.0.1:8000

La documentación interactiva (Swagger UI) estará disponible en: http://127.0.0.1:8000/docs

---

2. Estructura del Proyecto y Modelos

El proyecto sigue una estructura modular simple:

- main.py: Contiene la inicialización de FastAPI, el lifespan (creación de DB) y todos los endpoints (controladores).
- models.py: Define las tablas de la base de datos (SQLModel) y los esquemas de entrada/salida (Pydantic).
- database.py: Contiene la configuración de la conexión a SQLite y el inyector de dependencia de la sesión (get_session).
- database.db: Archivo SQLite generado automáticamente al iniciar la aplicación.

Diagrama de Relación (Entidades)
- Categoria (1) tiene muchos (N) Producto.
- Producto (1) puede estar en muchos (N) registros de Comprador (historial de ventas).

---

3. Reglas de Negocio Implementadas

La API implementa validaciones estrictas y lógica de negocio esencial:

- Regla: Unicidad (Categoria)
  - Implementación: El nombre de la categoría es único (unique=True).
  - Error: 409 Conflict

- Regla: Stock Mínimo (Producto)
  - Implementación: El stock y el precio deben ser mayores o iguales a cero.
  - Error: 422 Validation Error

- Regla: Venta Segura (Producto / Comprador)
  - Implementación: No se permite vender más unidades de las disponibles en stock.
  - Error: 400 Bad Request

- Regla: Edad Mínima (Comprador)
  - Implementación: El comprador debe tener 18 años o más.
  - Error: 422 Validation Error

- Regla: Baja en Cascada (Categoria)
  - Implementación: Al eliminar (DELETE) una categoría, todos sus productos activos pasan a is_active=False (Cascada).

- Regla: Descuento por Volumen (Comprador)
  - Implementación: Si la cantidad_unidades es >= 3, se aplica un 20% de descuento al subtotal de la compra.

---

4. Endpoints Principales

### ENDPOINTS DE CATEGORIAS

- Método: POST
  - Ruta: /categorias/
  - Descripción: Crea una nueva categoría.
  - Estado de Éxito: 201 Created

- Método: GET
  - Ruta: /categorias/
  - Descripción: Lista todas las categorías activas.
  - Estado de Éxito: 200 OK

- Método: PATCH
  - Ruta: /categorias/{id}
  - Descripción: Actualiza datos de la categoría (nombre, descripción).
  - Estado de Éxito: 200 OK

- Método: DELETE
  - Ruta: /categorias/{id}
  - Descripción: Baja Lógica: Marca la categoría y todos sus productos como is_active=False (Cascada).
  - Estado de Éxito: 204 No Content

### ENDPOINTS DE PRODUCTOS

- Método: POST
  - Ruta: /productos/
  - Descripción: Crea un nuevo producto (Requiere categoria_id activo).
  - Estado de Éxito: 201 Created

- Método: GET
  - Ruta: /productos/
  - Descripción: Lista productos activos (Acepta filtros por stock, precio_min/max, categoria_id).
  - Estado de Éxito: 200 OK

- Método: GET
  - Ruta: /productos/{id}
  - Descripción: Obtiene un producto por ID, incluyendo su información de categoría.
  - Estado de Éxito: 200 OK

- Método: PATCH
  - Ruta: /productos/{id}
  - Descripción: Actualiza datos del producto.
  - Estado de Éxito: 200 OK

- Método: DELETE
  - Ruta: /productos/{id}
  - Descripción: Baja Lógica: Marca el producto como is_active=False.
  - Estado de Éxito: 204 No Content

- Método: PATCH
  - Ruta: /productos/{id}/restar_stock
  - Descripción: Resta una cantidad específica del stock (simula envío/pérdida).
  - Estado de Éxito: 200 OK

### ENDPOINTS DE COMPRA/VENTA

- Método: POST
  - Ruta: /compras/
  - Descripción: Registra una venta. Valida edad y stock, aplica descuento (si aplica), y resta la cantidad del stock del producto.
  - Estado de Éxito: 201 Created

- Método: GET
  - Ruta: /compras/
  - Descripción: Lista el historial de compras registradas.
  - Estado de Éxito: 200 OK

---

5. Uso de Tecnologías

- Servidor Web: FastAPI (Para alto rendimiento y tipado de datos).
- Base de Datos: SQLModel (Unificación de Pydantic y SQLAlchemy para la definición de modelos).
- Driver: SQLite (Base de datos ligera para desarrollo).
- Validación: Pydantic (Asegura la calidad y el formato de los datos de entrada/salida).

---