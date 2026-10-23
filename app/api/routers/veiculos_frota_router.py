from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.usuario import Usuario
from app.schemas.usuario import PaginatedResponse
from app.schemas.veiculo_frota import (
    VeiculoFrotaCreate,
    VeiculoFrotaResponse,
    VeiculoFrotaUpdate,
)
from app.services.veiculo_frota_service import VeiculoFrotaService

router = APIRouter(prefix="/veiculos-frota", tags=["Frota de Veículos"])


@router.get(
    "",
    response_model=PaginatedResponse[VeiculoFrotaResponse],
    summary="Listar veículos da frota com paginação e filtros",
)
def listar_veiculos(
    page: int = Query(default=1, ge=1, description="Número da página"),
    size: int = Query(default=20, ge=1, le=100, description="Itens por página"),
    disponivel: Optional[bool] = Query(default=None, description="Filtrar por disponibilidade"),
    modelo: Optional[str] = Query(default=None, description="Filtrar por modelo"),
    capacidade_minima_kg: Optional[float] = Query(default=None, gt=0, description="Filtrar por capacidade mínima (kg)"),
    db: Session = Depends(get_db),
):
    service = VeiculoFrotaService(db)
    return service.listar(
        page=page,
        size=size,
        disponivel=disponivel,
        modelo=modelo,
        capacidade_minima_kg=capacidade_minima_kg,
    )


@router.get(
    "/{veiculo_id}",
    response_model=VeiculoFrotaResponse,
    summary="Obter veículo da frota por ID",
)
def obter_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    service = VeiculoFrotaService(db)
    return service.obter_por_id(veiculo_id)


@router.post(
    "",
    response_model=VeiculoFrotaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo veículo na frota",
)
def criar_veiculo(
    dados: VeiculoFrotaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    service = VeiculoFrotaService(db)
    return service.criar(dados)


@router.put(
    "/{veiculo_id}",
    response_model=VeiculoFrotaResponse,
    summary="Atualizar veículo da frota",
)
def atualizar_veiculo(
    veiculo_id: int,
    dados: VeiculoFrotaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    service = VeiculoFrotaService(db)
    return service.atualizar(veiculo_id, dados)


@router.delete(
    "/{veiculo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover veículo da frota",
)
def remover_veiculo(
    veiculo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    service = VeiculoFrotaService(db)
    service.remover(veiculo_id)
    return None
