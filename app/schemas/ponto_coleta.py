from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ZONAS_PERMITIDAS = {"RESIDENCIAL", "COMERCIAL", "INDUSTRIAL", "MISTA"}


class PontoColetaBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=120, description="Nome identificador do ponto de coleta")
    bairro: str = Field(..., min_length=2, max_length=100, description="Bairro do ponto de coleta")
    cidade: str = Field(..., min_length=2, max_length=100, description="Cidade do ponto de coleta")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude geográfica (-90 a 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude geográfica (-180 a 180)")
    populacao_atendida: int = Field(..., gt=0, le=5000000, description="População estimada atendida pelo ponto")
    tipo_zona: str = Field(..., description="Tipo de zona urbana: RESIDENCIAL, COMERCIAL, INDUSTRIAL ou MISTA")
    capacidade_armazenamento_kg: float = Field(..., gt=0.0, description="Capacidade máxima de armazenamento em kg")
    ativo: bool = Field(default=True, description="Indica se o ponto de coleta está ativo")

    @field_validator("tipo_zona")
    @classmethod
    def validar_tipo_zona(cls, v: str) -> str:
        zona = v.strip().upper()
        if zona not in ZONAS_PERMITIDAS:
            raise ValueError(f"tipo_zona inválido. Valores aceitos: {', '.join(sorted(ZONAS_PERMITIDAS))}")
        return zona


class PontoColetaCreate(PontoColetaBase):
    pass


class PontoColetaUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=3, max_length=120)
    bairro: Optional[str] = Field(default=None, min_length=2, max_length=100)
    cidade: Optional[str] = Field(default=None, min_length=2, max_length=100)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    populacao_atendida: Optional[int] = Field(default=None, gt=0, le=5000000)
    tipo_zona: Optional[str] = Field(default=None)
    capacidade_armazenamento_kg: Optional[float] = Field(default=None, gt=0.0)
    ativo: Optional[bool] = Field(default=None)

    @field_validator("tipo_zona")
    @classmethod
    def validar_tipo_zona(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        zona = v.strip().upper()
        if zona not in ZONAS_PERMITIDAS:
            raise ValueError(f"tipo_zona inválido. Valores aceitos: {', '.join(sorted(ZONAS_PERMITIDAS))}")
        return zona


class PontoColetaResponse(PontoColetaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
