from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.historico_coleta import HistoricoColeta


class HistoricoColetaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, historico_id: int) -> Optional[HistoricoColeta]:
        return self.db.query(HistoricoColeta).filter(HistoricoColeta.id == historico_id).first()

    def list_paginated(
        self,
        page: int = 1,
        size: int = 20,
        ponto_coleta_id: Optional[int] = None,
        dia_semana: Optional[int] = None,
        evento_sazonal: Optional[bool] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
    ) -> Tuple[List[HistoricoColeta], int]:
        query = self.db.query(HistoricoColeta)

        if ponto_coleta_id is not None:
            query = query.filter(HistoricoColeta.ponto_coleta_id == ponto_coleta_id)
        if dia_semana is not None:
            query = query.filter(HistoricoColeta.dia_semana == dia_semana)
        if evento_sazonal is not None:
            query = query.filter(HistoricoColeta.evento_sazonal == evento_sazonal)
        if data_inicio is not None:
            query = query.filter(HistoricoColeta.data_coleta >= data_inicio)
        if data_fim is not None:
            query = query.filter(HistoricoColeta.data_coleta <= data_fim)

        total = query.count()
        items = (
            query.order_by(HistoricoColeta.data_coleta.desc(), HistoricoColeta.id.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return items, total

    def create(self, dados: dict) -> HistoricoColeta:
        historico = HistoricoColeta(**dados)
        self.db.add(historico)
        self.db.commit()
        self.db.refresh(historico)
        return historico

    def update(self, historico: HistoricoColeta, dados: dict) -> HistoricoColeta:
        for campo, valor in dados.items():
            setattr(historico, campo, valor)
        self.db.commit()
        self.db.refresh(historico)
        return historico

    def delete(self, historico: HistoricoColeta) -> None:
        self.db.delete(historico)
        self.db.commit()
