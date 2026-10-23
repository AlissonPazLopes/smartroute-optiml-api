"""Schemas Pydantic para o pipeline de Machine Learning."""
from datetime import date, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TreinamentoRequest(BaseModel):
    cv_folds: int = Field(default=5, ge=2, le=10, description="Número de folds para validação cruzada K-Fold")
    n_estimators: int = Field(default=120, ge=20, le=500, description="Número de árvores do Random Forest")
    random_state: int = Field(default=42, description="Semente aleatória para reprodutibilidade")


class MetricasAlvo(BaseModel):
    r2: float = Field(..., description="Coeficiente de determinação R²")
    mae: float = Field(..., description="Erro Absoluto Médio (kg)")
    rmse: float = Field(..., description="Raiz do Erro Quadrático Médio (kg)")
    mape: float = Field(..., description="Erro Percentual Absoluto Médio (%)")


class ResumoAlgoritmo(BaseModel):
    r2_medio: float
    mae_medio: float
    rmse_medio: float
    mape_medio: float


class TreinamentoResponse(BaseModel):
    sucesso: bool
    mensagem: str
    treinado_em: str
    total_amostras: int
    cv_folds: int
    melhor_modelo_selecionado: str
    vencedor_por_alvo: Dict[str, str]
    resumo_comparativo: Dict[str, ResumoAlgoritmo]
    metricas_por_alvo: Dict[str, Dict[str, MetricasAlvo]]
    caminho_artefato: str


class ComparativoModelosResponse(BaseModel):
    treinado_em: str
    total_amostras: int
    cv_folds: int
    melhor_modelo_selecionado: str
    vencedor_por_alvo: Dict[str, str]
    resumo_comparativo: Dict[str, ResumoAlgoritmo]
    metricas_por_alvo: Dict[str, Dict[str, MetricasAlvo]]
    features_utilizadas: List[str]


class PrevisaoDemandaRequest(BaseModel):
    data_previsao: date = Field(
        default_factory=lambda: date.today() + timedelta(days=1),
        description="Data alvo para previsão da coleta",
    )
    temperatura_media: float = Field(default=25.0, ge=-20.0, le=55.0, description="Temperatura média prevista (°C)")
    evento_sazonal: bool = Field(default=False, description="Indica se haverá evento sazonal ou feriado na data")
    ponto_ids: Optional[List[int]] = Field(
        default=None,
        description="Lista opcional de IDs dos pontos de coleta (se omitido, prevê para todos os pontos ativos)",
    )
    algoritmo: Optional[str] = Field(
        default=None,
        description="Opcional: 'RandomForestRegressor' ou 'MultipleLinearRegression'. Se omitido, usa o melhor modelo.",
    )


class PrevisaoPontoItem(BaseModel):
    ponto_coleta_id: int
    ponto_nome: str
    bairro: str
    tipo_zona: str
    latitude: float
    longitude: float
    peso_papelao_kg: float
    peso_plastico_kg: float
    peso_aluminio_kg: float
    peso_total_kg: float
    valor_estimado_brl: float
    taxa_ocupacao_estimada_pct: float
    prioridade_coleta: float


class PrevisaoDemandaResponse(BaseModel):
    data_previsao: date
    dia_semana: int
    temperatura_media: float
    evento_sazonal: bool
    modelo_utilizado: str
    quantidade_pontos: int
    peso_total_previsto_kg: float
    valor_total_estimado_brl: float
    previsoes_por_ponto: List[PrevisaoPontoItem]
