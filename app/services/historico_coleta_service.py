from datetime import date
import math
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.historico_coleta import HistoricoColeta
from app.repositories.historico_coleta_repository import HistoricoColetaRepository
from app.repositories.ponto_coleta_repository import PontoColetaRepository
from app.schemas.historico_coleta import (
    HistoricoColetaCreate,
    HistoricoColetaResponse,
    HistoricoColetaUpdate,
)
from app.schemas.usuario import PaginatedResponse


class HistoricoColetaService:
    def __init__(self, db: Session):
        self.repo = HistoricoColetaRepository(db)
        self.ponto_repo = PontoColetaRepository(db)

    def listar(
        self,
        page: int = 1,
        size: int = 20,
        ponto_coleta_id: Optional[int] = None,
        dia_semana: Optional[int] = None,
        evento_sazonal: Optional[bool] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
    ) -> PaginatedResponse[HistoricoColetaResponse]:
        items, total = self.repo.list_paginated(
            page=page,
            size=size,
            ponto_coleta_id=ponto_coleta_id,
            dia_semana=dia_semana,
            evento_sazonal=evento_sazonal,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return PaginatedResponse(
            items=[HistoricoColetaResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def obter_por_id(self, historico_id: int) -> HistoricoColeta:
        historico = self.repo.get_by_id(historico_id)
        if not historico:
            raise NotFoundException(f"Registro de histórico com ID {historico_id} não encontrado.")
        return historico

    def criar(self, dados: HistoricoColetaCreate) -> HistoricoColeta:
        ponto = self.ponto_repo.get_by_id(dados.ponto_coleta_id)
        if not ponto:
            raise NotFoundException(f"Ponto de coleta com ID {dados.ponto_coleta_id} não encontrado.")
        return self.repo.create(dados.model_dump())

    def atualizar(self, historico_id: int, dados: HistoricoColetaUpdate) -> HistoricoColeta:
        historico = self.obter_por_id(historico_id)
        update_data = dados.model_dump(exclude_unset=True)

        if any(k in update_data for k in ("peso_papelao_kg", "peso_plastico_kg", "peso_aluminio_kg")):
            papelao = update_data.get("peso_papelao_kg", historico.peso_papelao_kg)
            plastico = update_data.get("peso_plastico_kg", historico.peso_plastico_kg)
            aluminio = update_data.get("peso_aluminio_kg", historico.peso_aluminio_kg)
            if "peso_total_kg" not in update_data:
                update_data["peso_total_kg"] = round(papelao + plastico + aluminio, 2)
            if "valor_estimado_brl" not in update_data:
                update_data["valor_estimado_brl"] = round(
                    papelao * 0.85 + plastico * 2.40 + aluminio * 7.50, 2
                )

        return self.repo.update(historico, update_data)

    def remover(self, historico_id: int) -> None:
        historico = self.obter_por_id(historico_id)
        self.repo.delete(historico)
