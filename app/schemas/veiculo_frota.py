import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

PLACA_REGEX = re.compile(r"^[A-Z]{3}-?[0-9][A-Z0-9][0-9]{2}$")


class VeiculoFrotaBase(BaseModel):
    placa: str = Field(..., min_length=7, max_length=8, description="Placa do veículo (Mercosul ou padrão antigo)")
    modelo: str = Field(..., min_length=2, max_length=100, description="Modelo do caminhão/veículo coletor")
    capacidade_carga_kg: float = Field(..., gt=0.0, description="Capacidade máxima de carga em kg")
    volume_maximo_m3: float = Field(..., gt=0.0, description="Volume máximo da caçamba/baú em m³")
    custo_por_km: float = Field(..., gt=0.0, description="Custo operacional por km rodado em R$")
    disponivel: bool = Field(default=True, description="Indica se o veículo está disponível para operação")

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, v: str) -> str:
        placa_limpa = v.strip().upper()
        if not PLACA_REGEX.match(placa_limpa):
            raise ValueError("Placa inválida. Use o formato ABC-1234, ABC1234 ou Mercosul ABC1D23.")
        return placa_limpa.replace("-", "")


class VeiculoFrotaCreate(VeiculoFrotaBase):
    pass


class VeiculoFrotaUpdate(BaseModel):
    placa: Optional[str] = Field(default=None, min_length=7, max_length=8)
    modelo: Optional[str] = Field(default=None, min_length=2, max_length=100)
    capacidade_carga_kg: Optional[float] = Field(default=None, gt=0.0)
    volume_maximo_m3: Optional[float] = Field(default=None, gt=0.0)
    custo_por_km: Optional[float] = Field(default=None, gt=0.0)
    disponivel: Optional[bool] = Field(default=None)

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        placa_limpa = v.strip().upper()
        if not PLACA_REGEX.match(placa_limpa):
            raise ValueError("Placa inválida. Use o formato ABC-1234, ABC1234 ou Mercosul ABC1D23.")
        return placa_limpa.replace("-", "")


class VeiculoFrotaResponse(VeiculoFrotaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
