import math
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.models.ponto_coleta import PontoColeta
from app.repositories.ponto_coleta_repository import PontoColetaRepository
from app.schemas.ponto_coleta import PontoColetaCreate, PontoColetaResponse, PontoColetaUpdate
from app.schemas.usuario import PaginatedResponse


class PontoColetaService:
    def __init__(self, db: Session):
        self.repo = PontoColetaRepository(db)

    def listar(
        self,
        page: int = 1,
        size: int = 20,
        cidade: Optional[str] = None,
        bairro: Optional[str] = None,
        tipo_zona: Optional[str] = None,
        ativo: Optional[bool] = None,
    ) -> PaginatedResponse[PontoColetaResponse]:
        items, total = self.repo.list_paginated(
            page=page,
            size=size,
            cidade=cidade,
            bairro=bairro,
            tipo_zona=tipo_zona,
            ativo=ativo,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return PaginatedResponse(
            items=[PontoColetaResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def obter_por_id(self, ponto_id: int) -> PontoColeta:
        ponto = self.repo.get_by_id(ponto_id)
        if not ponto:
            raise NotFoundException(f"Ponto de coleta com ID {ponto_id} não encontrado.")
        return ponto

    def criar(self, dados: PontoColetaCreate) -> PontoColeta:
        existente = self.repo.get_by_nome(dados.nome)
        if existente:
            raise ConflictException(f"Já existe um ponto de coleta com o nome '{dados.nome}'.")
        return self.repo.create(dados.model_dump())

    def atualizar(self, ponto_id: int, dados: PontoColetaUpdate) -> PontoColeta:
        ponto = self.obter_por_id(ponto_id)
        update_data = dados.model_dump(exclude_unset=True)
        if "nome" in update_data and update_data["nome"] != ponto.nome:
            existente = self.repo.get_by_nome(update_data["nome"])
            if existente:
                raise ConflictException(f"Já existe um ponto de coleta com o nome '{update_data['nome']}'.")
        return self.repo.update(ponto, update_data)

    def remover(self, ponto_id: int) -> None:
        ponto = self.obter_por_id(ponto_id)
        self.repo.delete(ponto)
