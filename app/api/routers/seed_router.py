from typing import Optional

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.seeder import SeedRequest, SeedResponse
from app.services.data_seeder import DataSeederService

router = APIRouter(prefix="/seed", tags=["Data Seeder (Sintético ML)"])


@router.post(
    "/gerar-dados",
    response_model=SeedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Popular banco de dados com dados sintéticos realistas para ML e Roteirização",
)
def gerar_dados_sinteticos(
    config: Optional[SeedRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    service = DataSeederService(db)
    cfg = config if config is not None else SeedRequest()
    return service.gerar_dados(cfg)
