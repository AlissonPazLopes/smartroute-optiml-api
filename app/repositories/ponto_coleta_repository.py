from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.ponto_coleta import PontoColeta


class PontoColetaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, ponto_id: int) -> Optional[PontoColeta]:
        return self.db.query(PontoColeta).filter(PontoColeta.id == ponto_id).first()

    def get_by_nome(self, nome: str) -> Optional[PontoColeta]:
        return self.db.query(PontoColeta).filter(PontoColeta.nome == nome).first()

    def list_paginated(
        self,
        page: int = 1,
        size: int = 20,
        cidade: Optional[str] = None,
        bairro: Optional[str] = None,
        tipo_zona: Optional[str] = None,
        ativo: Optional[bool] = None,
    ) -> Tuple[List[PontoColeta], int]:
        query = self.db.query(PontoColeta)

        if cidade:
            query = query.filter(PontoColeta.cidade.ilike(f"%{cidade}%"))
        if bairro:
            query = query.filter(PontoColeta.bairro.ilike(f"%{bairro}%"))
        if tipo_zona:
            query = query.filter(PontoColeta.tipo_zona == tipo_zona.strip().upper())
        if ativo is not None:
            query = query.filter(PontoColeta.ativo == ativo)

        total = query.count()
        items = query.order_by(PontoColeta.id.asc()).offset((page - 1) * size).limit(size).all()
        return items, total

    def create(self, dados: dict) -> PontoColeta:
        ponto = PontoColeta(**dados)
        self.db.add(ponto)
        self.db.commit()
        self.db.refresh(ponto)
        return ponto

    def update(self, ponto: PontoColeta, dados: dict) -> PontoColeta:
        for campo, valor in dados.items():
            setattr(ponto, campo, valor)
        self.db.commit()
        self.db.refresh(ponto)
        return ponto

    def delete(self, ponto: PontoColeta) -> None:
        self.db.delete(ponto)
        self.db.commit()
