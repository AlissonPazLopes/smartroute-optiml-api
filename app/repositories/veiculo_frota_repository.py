from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.veiculo_frota import VeiculoFrota


class VeiculoFrotaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, veiculo_id: int) -> Optional[VeiculoFrota]:
        return self.db.query(VeiculoFrota).filter(VeiculoFrota.id == veiculo_id).first()

    def get_by_placa(self, placa: str) -> Optional[VeiculoFrota]:
        return self.db.query(VeiculoFrota).filter(VeiculoFrota.placa == placa.upper().replace("-", "")).first()

    def list_paginated(
        self,
        page: int = 1,
        size: int = 20,
        disponivel: Optional[bool] = None,
        modelo: Optional[str] = None,
        capacidade_minima_kg: Optional[float] = None,
    ) -> Tuple[List[VeiculoFrota], int]:
        query = self.db.query(VeiculoFrota)

        if disponivel is not None:
            query = query.filter(VeiculoFrota.disponivel == disponivel)
        if modelo:
            query = query.filter(VeiculoFrota.modelo.ilike(f"%{modelo}%"))
        if capacidade_minima_kg is not None:
            query = query.filter(VeiculoFrota.capacidade_carga_kg >= capacidade_minima_kg)

        total = query.count()
        items = query.order_by(VeiculoFrota.id.asc()).offset((page - 1) * size).limit(size).all()
        return items, total

    def create(self, dados: dict) -> VeiculoFrota:
        veiculo = VeiculoFrota(**dados)
        self.db.add(veiculo)
        self.db.commit()
        self.db.refresh(veiculo)
        return veiculo

    def update(self, veiculo: VeiculoFrota, dados: dict) -> VeiculoFrota:
        for campo, valor in dados.items():
            setattr(veiculo, campo, valor)
        self.db.commit()
        self.db.refresh(veiculo)
        return veiculo

    def delete(self, veiculo: VeiculoFrota) -> None:
        self.db.delete(veiculo)
        self.db.commit()
