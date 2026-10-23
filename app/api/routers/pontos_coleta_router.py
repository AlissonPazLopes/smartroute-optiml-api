from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.usuario import Usuario
from app.schemas.ponto_coleta import (
    PontoColetaCreate,
    PontoColetaResponse,
    PontoColetaUpdate,
)
from app.schemas.usuario import PaginatedResponse
from app.services.ponto_coleta_service import PontoColetaService

router = APIRouter(prefix="/pontos-coleta", tags=["Pontos de Coleta"])


@router.get(
    "",
    response_model=PaginatedResponse[PontoColetaResponse],
    summary="Listar pontos de coleta com paginação e filtros",
)
def listar_pontos(
    page: int = Query(default=1, ge=1, description="Número da página"),
    size: int = Query(default=20, ge=1, le=200, description="Itens por página"),
    cidade: Optional[str] = Query(default=None, description="Filtrar por cidade"),
    bairro: Optional[str] = Query(default=None, description="Filtrar por bairro"),
    tipo_zona: Optional[str] = Query(default=None, description="Filtrar por tipo de zona"),
    ativo: Optional[bool] = Query(default=None, description="Filtrar por status ativo"),
    db: Session = Depends(get_db),
):
    service = PontoColetaService(db)
    return service.listar(
        page=page,
        size=size,
        cidade=cidade,
        bairro=bairro,
        tipo_zona=tipo_zona,
        ativo=ativo,
    )


@router.get(
    "/{ponto_id}",
    response_model=PontoColetaResponse,
    summary="Buscar ponto de coleta por ID",
)
def obter_ponto(ponto_id: int, db: Session = Depends(get_db)):
    service = PontoColetaService(db)
    return service.obter_por_id(ponto_id)


@router.post(
    "",
    response_model=PontoColetaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo ponto de coleta",
)
def criar_ponto(
    dados: PontoColetaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    service = PontoColetaService(db)
    return service.criar(dados)


@router.put(
    "/{ponto_id}",
    response_model=PontoColetaResponse,
    summary="Atualizar ponto de coleta existente",
)
def atualizar_ponto(
    ponto_id: int,
    dados: PontoColetaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    service = PontoColetaService(db)
    return service.atualizar(ponto_id, dados)


@router.delete(
    "/{ponto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover ponto de coleta",
)
def remover_ponto(
    ponto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    service = PontoColetaService(db)
    service.remover(ponto_id)
    return None
