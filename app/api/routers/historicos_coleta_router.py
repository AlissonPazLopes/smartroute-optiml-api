from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.usuario import Usuario
from app.schemas.historico_coleta import (
    HistoricoColetaCreate,
    HistoricoColetaResponse,
    HistoricoColetaUpdate,
)
from app.schemas.usuario import PaginatedResponse
from app.services.historico_coleta_service import HistoricoColetaService

router = APIRouter(prefix="/historicos-coleta", tags=["Histórico de Coletas"])


@router.get(
    "",
    response_model=PaginatedResponse[HistoricoColetaResponse],
    summary="Listar histórico de coletas com paginação e filtros",
)
def listar_historicos(
    page: int = Query(default=1, ge=1, description="Número da página"),
    size: int = Query(default=20, ge=1, le=500, description="Itens por página"),
    ponto_coleta_id: Optional[int] = Query(default=None, description="Filtrar por ID do ponto de coleta"),
    dia_semana: Optional[int] = Query(default=None, ge=0, le=6, description="Filtrar por dia da semana (0-6)"),
    evento_sazonal: Optional[bool] = Query(default=None, description="Filtrar por evento sazonal"),
    data_inicio: Optional[date] = Query(default=None, description="Data inicial"),
    data_fim: Optional[date] = Query(default=None, description="Data final"),
    db: Session = Depends(get_db),
):
    service = HistoricoColetaService(db)
    return service.listar(
        page=page,
        size=size,
        ponto_coleta_id=ponto_coleta_id,
        dia_semana=dia_semana,
        evento_sazonal=evento_sazonal,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@router.get(
    "/{historico_id}",
    response_model=HistoricoColetaResponse,
    summary="Obter registro histórico de coleta por ID",
)
def obter_historico(historico_id: int, db: Session = Depends(get_db)):
    service = HistoricoColetaService(db)
    return service.obter_por_id(historico_id)


@router.post(
    "",
    response_model=HistoricoColetaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nova coleta no histórico",
)
def criar_historico(
    dados: HistoricoColetaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    service = HistoricoColetaService(db)
    return service.criar(dados)


@router.put(
    "/{historico_id}",
    response_model=HistoricoColetaResponse,
    summary="Atualizar registro histórico de coleta",
)
def atualizar_historico(
    historico_id: int,
    dados: HistoricoColetaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    service = HistoricoColetaService(db)
    return service.atualizar(historico_id, dados)


@router.delete(
    "/{historico_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover registro histórico de coleta",
)
def remover_historico(
    historico_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    service = HistoricoColetaService(db)
    service.remover(historico_id)
    return None
