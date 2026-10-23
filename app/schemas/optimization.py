"""Schemas Pydantic para os motores de otimização combinatória (PLI PuLP e VNS CVRP)."""
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CandidatoCargaItem(BaseModel):
    ponto_coleta_id: int = Field(..., gt=0, description="ID do ponto de coleta")
    ponto_nome: Optional[str] = Field(default=None, description="Nome do ponto de coleta")
    latitude: float = Field(default=-23.5505, ge=-90.0, le=90.0)
    longitude: float = Field(default=-46.6333, ge=-180.0, le=180.0)
    peso_papelao_kg: float = Field(..., ge=0.0, description="Carga de papelão em kg")
    peso_plastico_kg: float = Field(..., ge=0.0, description="Carga de plástico em kg")
    peso_aluminio_kg: float = Field(..., ge=0.0, description="Carga de alumínio em kg")
    prioridade_coleta: float = Field(default=5.0, ge=0.1, le=20.0, description="Prioridade de esvaziamento do ponto")


class AlocacaoCargaPLIRequest(BaseModel):
    veiculo_id: Optional[int] = Field(
        default=None,
        description="Opcional: ID de um veículo cadastrado no banco para usar sua capacidade",
    )
    capacidade_peso_kg: float = Field(default=4500.0, gt=0.0, description="Capacidade máxima de peso (kg)")
    capacidade_volume_m3: float = Field(default=16.0, gt=0.0, description="Capacidade máxima de volume (m³)")
    peso_financeiro: float = Field(default=0.65, ge=0.0, le=1.0, description="Peso do retorno financeiro na função objetivo")
    peso_ambiental: float = Field(default=0.35, ge=0.0, le=1.0, description="Peso do impacto ambiental CO2e na função objetivo")
    permitir_coleta_parcial_por_material: bool = Field(
        default=False,
        description="Se verdadeiro, permite coletar apenas frações específicas de materiais em um ponto",
    )
    candidatos: Optional[List[CandidatoCargaItem]] = Field(
        default=None,
        description="Lista de pontos e cargas. Se omitido, utiliza os pontos ativos do banco.",
    )


class PontoSelecionadoPLI(BaseModel):
    ponto_coleta_id: int
    ponto_nome: str
    latitude: float
    longitude: float
    prioridade_coleta: float
    materiais_coletados: List[str]
    peso_papelao_alocado_kg: float
    peso_plastico_alocado_kg: float
    peso_aluminio_alocado_kg: float
    peso_total_ponto_kg: float
    volume_total_ponto_m3: float
    valor_financeiro_ponto_brl: float
    impacto_ambiental_co2_kg: float


class AlocacaoCargaPLIResponse(BaseModel):
    status_solver: str
    otimo_encontrado: bool
    capacidade_peso_kg: float
    capacidade_volume_m3: float
    peso_total_alocado_kg: float
    volume_total_alocado_m3: float
    ocupacao_peso_pct: float
    ocupacao_volume_pct: float
    valor_financeiro_total_brl: float
    impacto_ambiental_co2_kg: float
    valor_funcao_objetivo: float
    quantidade_pontos_selecionados: int
    pontos_selecionados: List[PontoSelecionadoPLI]
    pontos_nao_atendidos_ids: List[int]


class DepositoCoord(BaseModel):
    nome: str = Field(default="Central de Triagem SmartRoute (Depósito)")
    latitude: float = Field(default=-23.5505, ge=-90.0, le=90.0)
    longitude: float = Field(default=-46.6333, ge=-180.0, le=180.0)


class PontoRoteamentoInput(BaseModel):
    ponto_coleta_id: int
    ponto_nome: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    demanda_kg: float = Field(default=300.0, ge=0.0)


class VeiculoRoteamentoInput(BaseModel):
    id: int = 1
    placa: str = "SRT1A01"
    modelo: str = "Caminhão Compactador"
    capacidade_carga_kg: float = Field(default=5000.0, gt=0.0)
    custo_por_km: float = Field(default=4.50, gt=0.0)


class RoteamentoVNSRequest(BaseModel):
    deposito: DepositoCoord = Field(default_factory=DepositoCoord)
    max_iteracoes: int = Field(default=80, ge=5, le=1000, description="Número máximo de iterações do VNS")
    random_seed: int = Field(default=42, description="Semente aleatória para o Shaking do VNS")
    pontos: Optional[List[PontoRoteamentoInput]] = Field(
        default=None,
        description="Lista opcional de pontos com coordenadas e demanda. Se omitida, usa os pontos ativos do banco.",
    )
    veiculos: Optional[List[VeiculoRoteamentoInput]] = Field(
        default=None,
        description="Lista opcional de veículos. Se omitida, usa os veículos disponíveis no banco.",
    )


class ParadaRotaItem(BaseModel):
    ordem: int
    ponto_coleta_id: int
    ponto_nome: str
    latitude: float
    longitude: float
    demanda_coletada_kg: float


class RotaVeiculoDetalhe(BaseModel):
    veiculo_id: int
    veiculo_placa: str
    veiculo_modelo: str
    capacidade_veiculo_kg: float
    carga_total_rota_kg: float
    taxa_ocupacao_veiculo_pct: float
    distancia_rota_km: float
    custo_estimado_rota_brl: float
    quantidade_paradas: int
    sequencia_ids: List[int]
    sequencia_visitas: List[ParadaRotaItem]


class RoteamentoVNSResponse(BaseModel):
    algoritmo: str
    max_iteracoes: int
    distancia_rota_nao_otimizada_km: float
    distancia_total_otimizada_km: float
    economia_distancia_km: float
    percentual_economia_pct: float
    custo_total_estimado_brl: float
    quantidade_rotas: int
    rotas: List[RotaVeiculoDetalhe]


class PlanejamentoIntegradoRequest(BaseModel):
    data_planejamento: date = Field(
        default_factory=lambda: date.today() + timedelta(days=1),
        description="Data futura para previsão de demanda e roteirização",
    )
    temperatura_media: float = Field(default=26.0, ge=-20.0, le=55.0)
    evento_sazonal: bool = Field(default=False)
    fator_capacidade_frota: float = Field(
        default=0.85,
        gt=0.1,
        le=1.5,
        description="Fração da capacidade da frota disponível a ser alocada via PLI",
    )
    max_iteracoes_vns: int = Field(default=80, ge=5, le=500)
    random_seed: int = Field(default=42)
    deposito: DepositoCoord = Field(default_factory=DepositoCoord)


class PlanejamentoIntegradoResponse(BaseModel):
    data_planejamento: date
    etapa_1_previsao_ml: Dict[str, Any]
    etapa_2_selecao_carga_pli: AlocacaoCargaPLIResponse
    etapa_3_roteamento_frota_vns: RoteamentoVNSResponse
    resumo_executivo: Dict[str, Any]
