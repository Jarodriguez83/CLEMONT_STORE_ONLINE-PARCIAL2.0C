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

def obtener_categorias(session: Session, activa: Optional[bool] = True, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Categoria]:
    stmt = select(Categoria)
    if activa is True:
        stmt = stmt.where(Categoria.activa == True)
    elif activa is False:
        stmt = stmt.where(Categoria.activa == False)
    if limit is not None:
        stmt = stmt.limit(limit)
    if offset is not None:
        stmt = stmt.offset(offset)
    results = session.exec(stmt).all()
    return results

