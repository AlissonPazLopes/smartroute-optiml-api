from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HistoricoColetaBase(BaseModel):
    ponto_coleta_id: int = Field(..., gt=0, description="ID do ponto de coleta")
    data_coleta: date = Field(..., description="Data de realização da coleta")
    dia_semana: Optional[int] = Field(default=None, ge=0, le=6, description="Dia da semana (0=Segunda a 6=Domingo)")
    temperatura_media: float = Field(..., ge=-20.0, le=55.0, description="Temperatura média do dia em °C")
    evento_sazonal: bool = Field(default=False, description="Indica ocorrência de feriado ou evento sazonal")
    peso_papelao_kg: float = Field(..., ge=0.0, description="Peso coletado de papelão em kg")
    peso_plastico_kg: float = Field(..., ge=0.0, description="Peso coletado de plástico em kg")
    peso_aluminio_kg: float = Field(..., ge=0.0, description="Peso coletado de alumínio em kg")
    peso_total_kg: Optional[float] = Field(default=None, ge=0.0, description="Peso total coletado em kg")
    valor_estimado_brl: Optional[float] = Field(default=None, ge=0.0, description="Valor financeiro estimado em R$")

    @model_validator(mode="after")
    def preencher_e_validar_campos_calculados(self) -> "HistoricoColetaBase":
        if self.dia_semana is None and self.data_coleta is not None:
            self.dia_semana = self.data_coleta.weekday()

        soma_pesos = round(self.peso_papelao_kg + self.peso_plastico_kg + self.peso_aluminio_kg, 2)
        if self.peso_total_kg is None:
            self.peso_total_kg = soma_pesos
        elif abs(self.peso_total_kg - soma_pesos) > 0.5:
            self.peso_total_kg = round(self.peso_total_kg, 2)

        if self.valor_estimado_brl is None:
            # Preços médios de recicláveis por kg: Papelão R$ 0.85, Plástico R$ 2.40, Alumínio R$ 7.50
            self.valor_estimado_brl = round(
                self.peso_papelao_kg * 0.85 + self.peso_plastico_kg * 2.40 + self.peso_aluminio_kg * 7.50,
                2,
            )
        return self


class HistoricoColetaCreate(HistoricoColetaBase):
    pass


class HistoricoColetaUpdate(BaseModel):
    data_coleta: Optional[date] = Field(default=None)
    dia_semana: Optional[int] = Field(default=None, ge=0, le=6)
    temperatura_media: Optional[float] = Field(default=None, ge=-20.0, le=55.0)
    evento_sazonal: Optional[bool] = Field(default=None)
    peso_papelao_kg: Optional[float] = Field(default=None, ge=0.0)
    peso_plastico_kg: Optional[float] = Field(default=None, ge=0.0)
    peso_aluminio_kg: Optional[float] = Field(default=None, ge=0.0)
    peso_total_kg: Optional[float] = Field(default=None, ge=0.0)
    valor_estimado_brl: Optional[float] = Field(default=None, ge=0.0)


class HistoricoColetaResponse(BaseModel):
    id: int
    ponto_coleta_id: int
    data_coleta: date
    dia_semana: int
    temperatura_media: float
    evento_sazonal: bool
    peso_papelao_kg: float
    peso_plastico_kg: float
    peso_aluminio_kg: float
    peso_total_kg: float
    valor_estimado_brl: float

    model_config = ConfigDict(from_attributes=True)
