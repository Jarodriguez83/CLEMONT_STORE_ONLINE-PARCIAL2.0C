from typing import List, Optional
from sqlmodel import Session, select
from fastapi import HTTPException, status
from sqlalchemy import func 
from models import Categoria, Producto
from schemas import CategoriaCrear, CategoriaActualizar

# FUNCIONES CRUD PARA CATEGORIAS
def crear_categoria(session: Session, categoria_in: CategoriaCrear) -> Categoria:
    stmt = select(Categoria).where(func.lower(Categoria.nombre) == categoria_in.nombre.lower())
    existente = session.exec(stmt).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La categoría con nombre '{categoria_in.nombre}' ya existe."
        )
    nueva_categoria = Categoria (
        nombre=categoria_in.nombre.strip(),
        descripcion=categoria_in.description.strip() if categoria_in.description else None, 
        activa=True
    )
    session.add(nueva_categoria)
    session.commit()
    session.refresh(nueva_categoria)
    return nueva_categoria

