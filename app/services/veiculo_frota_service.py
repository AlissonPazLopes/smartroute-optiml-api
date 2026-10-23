import math
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.models.veiculo_frota import VeiculoFrota
from app.repositories.veiculo_frota_repository import VeiculoFrotaRepository
from app.schemas.usuario import PaginatedResponse
from app.schemas.veiculo_frota import VeiculoFrotaCreate, VeiculoFrotaResponse, VeiculoFrotaUpdate


class VeiculoFrotaService:
    def __init__(self, db: Session):
        self.repo = VeiculoFrotaRepository(db)

    def listar(
        self,
        page: int = 1,
        size: int = 20,
        disponivel: Optional[bool] = None,
        modelo: Optional[str] = None,
        capacidade_minima_kg: Optional[float] = None,
    ) -> PaginatedResponse[VeiculoFrotaResponse]:
        items, total = self.repo.list_paginated(
            page=page,
            size=size,
            disponivel=disponivel,
            modelo=modelo,
            capacidade_minima_kg=capacidade_minima_kg,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return PaginatedResponse(
            items=[VeiculoFrotaResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def obter_por_id(self, veiculo_id: int) -> VeiculoFrota:
        veiculo = self.repo.get_by_id(veiculo_id)
        if not veiculo:
            raise NotFoundException(f"Veículo com ID {veiculo_id} não encontrado.")
        return veiculo

    def criar(self, dados: VeiculoFrotaCreate) -> VeiculoFrota:
        existente = self.repo.get_by_placa(dados.placa)
        if existente:
            raise ConflictException(f"Já existe um veículo cadastrado com a placa '{dados.placa}'.")
        return self.repo.create(dados.model_dump())

    def atualizar(self, veiculo_id: int, dados: VeiculoFrotaUpdate) -> VeiculoFrota:
        veiculo = self.obter_por_id(veiculo_id)
        update_data = dados.model_dump(exclude_unset=True)
        if "placa" in update_data and update_data["placa"] != veiculo.placa:
            existente = self.repo.get_by_placa(update_data["placa"])
            if existente:
                raise ConflictException(f"Já existe um veículo cadastrado com a placa '{update_data['placa']}'.")
        return self.repo.update(veiculo, update_data)

    def remover(self, veiculo_id: int) -> None:
        veiculo = self.obter_por_id(veiculo_id)
        self.repo.delete(veiculo)
