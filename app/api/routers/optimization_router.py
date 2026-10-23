"""Router REST para os motores de otimização: Programação Linear Inteira (PuLP), VNS (CVRP) e Planejamento Integrado."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.ml.model_trainer import ModelTrainerService
from app.models.ponto_coleta import PontoColeta
from app.models.veiculo_frota import VeiculoFrota
from app.optimization.knapsack_milp import resolver_alocacao_carga_pli
from app.optimization.vrp_vns import executar_roteamento_vns
from app.schemas.optimization import (
    AlocacaoCargaPLIRequest,
    AlocacaoCargaPLIResponse,
    PlanejamentoIntegradoRequest,
    PlanejamentoIntegradoResponse,
    RoteamentoVNSRequest,
    RoteamentoVNSResponse,
)

router = APIRouter(prefix="/otimizacao", tags=["Otimização Combinatória (PLI PuLP & VNS CVRP)"])


@router.post(
    "/alocacao-carga-pli",
    response_model=AlocacaoCargaPLIResponse,
    status_code=status.HTTP_200_OK,
    summary="Executar solver de Programação Linear Inteira (PuLP) para Problema da Mochila Multi-Material",
)
def otimizar_alocacao_carga_pli(
    req: Optional[AlocacaoCargaPLIRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    dados = req if req is not None else AlocacaoCargaPLIRequest()
    cap_peso = dados.capacidade_peso_kg
    cap_vol = dados.capacidade_volume_m3

    if dados.veiculo_id is not None:
        veic = db.query(VeiculoFrota).filter(VeiculoFrota.id == dados.veiculo_id).first()
        if not veic:
            raise NotFoundException(f"Veículo com ID {dados.veiculo_id} não encontrado.")
        cap_peso = veic.capacidade_carga_kg
        cap_vol = veic.volume_maximo_m3

    if dados.candidatos is not None:
        candidatos_list = [c.model_dump() for c in dados.candidatos]
    else:
        pontos_db = db.query(PontoColeta).filter(PontoColeta.ativo == True).order_by(PontoColeta.id.asc()).all()  # noqa: E712
        if not pontos_db:
            raise NotFoundException("Nenhum ponto de coleta ativo encontrado para otimização.")
        candidatos_list = []
        for p in pontos_db:
            fator = p.populacao_atendida / 1000.0
            candidatos_list.append(
                {
                    "ponto_coleta_id": p.id,
                    "ponto_nome": p.nome,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "peso_papelao_kg": round(fator * 4.2, 2),
                    "peso_plastico_kg": round(fator * 2.6, 2),
                    "peso_aluminio_kg": round(fator * 0.75, 2),
                    "prioridade_coleta": round(min(10.0, fator / 6.0), 2),
                }
            )

    return resolver_alocacao_carga_pli(
        capacidade_peso_kg=cap_peso,
        capacidade_volume_m3=cap_vol,
        candidatos=candidatos_list,
        peso_financeiro=dados.peso_financeiro,
        peso_ambiental=dados.peso_ambiental,
        permitir_coleta_parcial_por_material=dados.permitir_coleta_parcial_por_material,
    )


@router.post(
    "/roteamento-vns",
    response_model=RoteamentoVNSResponse,
    status_code=status.HTTP_200_OK,
    summary="Executar meta-heurística Variable Neighborhood Search (VNS) para Roteamento de Veículos Capacitado (CVRP)",
)
def otimizar_roteamento_vns(
    req: Optional[RoteamentoVNSRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    dados = req if req is not None else RoteamentoVNSRequest()

    if dados.pontos is not None:
        pontos_list = [p.model_dump() for p in dados.pontos]
    else:
        pontos_db = db.query(PontoColeta).filter(PontoColeta.ativo == True).order_by(PontoColeta.id.asc()).all()  # noqa: E712
        if not pontos_db:
            raise NotFoundException("Nenhum ponto de coleta encontrado para roteirização.")
        pontos_list = [
            {
                "ponto_coleta_id": p.id,
                "ponto_nome": p.nome,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "demanda_kg": round((p.populacao_atendida / 1000.0) * 7.5, 2),
            }
            for p in pontos_db
        ]

    if dados.veiculos is not None:
        veiculos_list = [v.model_dump() for v in dados.veiculos]
    else:
        veics_db = (
            db.query(VeiculoFrota)
            .filter(VeiculoFrota.disponivel == True)  # noqa: E712
            .order_by(VeiculoFrota.id.asc())
            .all()
        )
        if veics_db:
            veiculos_list = [
                {
                    "id": v.id,
                    "placa": v.placa,
                    "modelo": v.modelo,
                    "capacidade_carga_kg": v.capacidade_carga_kg,
                    "custo_por_km": v.custo_por_km,
                }
                for v in veics_db
            ]
        else:
            veiculos_list = [
                {
                    "id": 1,
                    "placa": "SRT1A01",
                    "modelo": "Caminhão Compactador Padrão",
                    "capacidade_carga_kg": 10000.0,
                    "custo_por_km": 4.80,
                }
            ]

    return executar_roteamento_vns(
        deposito=dados.deposito.model_dump(),
        pontos=pontos_list,
        veiculos=veiculos_list,
        max_iteracoes=dados.max_iteracoes,
        random_seed=dados.random_seed,
    )


@router.post(
    "/planejamento-integrado",
    response_model=PlanejamentoIntegradoResponse,
    status_code=status.HTTP_200_OK,
    summary="Pipeline Completo: Previsão de Demanda (ML) -> Seleção de Carga (PLI PuLP) -> Roteamento Ótimo (VNS)",
)
def executar_planejamento_integrado(
    req: Optional[PlanejamentoIntegradoRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    dados = req if req is not None else PlanejamentoIntegradoRequest()

    # 1. Previsão de Demanda com Machine Learning
    trainer = ModelTrainerService(db)
    previsao_ml = trainer.prever_demanda_pontos(
        data_previsao=dados.data_planejamento,
        temperatura_media=dados.temperatura_media,
        evento_sazonal=dados.evento_sazonal,
        auto_train_if_missing=True,
    )

    # 2. Obter frota disponível
    veics_db = (
        db.query(VeiculoFrota)
        .filter(VeiculoFrota.disponivel == True)  # noqa: E712
        .order_by(VeiculoFrota.id.asc())
        .all()
    )
    if not veics_db:
        raise NotFoundException("Nenhum veículo disponível na frota para planejamento integrado.")

    cap_peso_frota = sum(v.capacidade_carga_kg for v in veics_db) * dados.fator_capacidade_frota
    cap_vol_frota = sum(v.volume_maximo_m3 for v in veics_db) * dados.fator_capacidade_frota

    candidatos_pli: List[Dict[str, Any]] = []
    for item in previsao_ml["previsoes_por_ponto"]:
        candidatos_pli.append(
            {
                "ponto_coleta_id": item["ponto_coleta_id"],
                "ponto_nome": item["ponto_nome"],
                "latitude": item["latitude"],
                "longitude": item["longitude"],
                "peso_papelao_kg": item["peso_papelao_kg"],
                "peso_plastico_kg": item["peso_plastico_kg"],
                "peso_aluminio_kg": item["peso_aluminio_kg"],
                "prioridade_coleta": item["prioridade_coleta"],
            }
        )

    # 3. Seleção ótima de cargas via Programação Linear Inteira (PuLP)
    resultado_pli = resolver_alocacao_carga_pli(
        capacidade_peso_kg=cap_peso_frota,
        capacidade_volume_m3=cap_vol_frota,
        candidatos=candidatos_pli,
        peso_financeiro=0.65,
        peso_ambiental=0.35,
        permitir_coleta_parcial_por_material=False,
    )

    # 4. Roteirização da frota via Meta-heurística VNS apenas para os pontos selecionados pelo PLI
    pontos_para_vns = [
        {
            "ponto_coleta_id": p["ponto_coleta_id"],
            "ponto_nome": p["ponto_nome"],
            "latitude": p["latitude"],
            "longitude": p["longitude"],
            "demanda_kg": p["peso_total_ponto_kg"],
        }
        for p in resultado_pli["pontos_selecionados"]
    ]
    veiculos_para_vns = [
        {
            "id": v.id,
            "placa": v.placa,
            "modelo": v.modelo,
            "capacidade_carga_kg": v.capacidade_carga_kg,
            "custo_por_km": v.custo_por_km,
        }
        for v in veics_db
    ]

    resultado_vns = executar_roteamento_vns(
        deposito=dados.deposito.model_dump(),
        pontos=pontos_para_vns,
        veiculos=veiculos_para_vns,
        max_iteracoes=dados.max_iteracoes_vns,
        random_seed=dados.random_seed,
    )

    receita_reciclaveis = resultado_pli["valor_financeiro_total_brl"]
    custo_transporte = resultado_vns["custo_total_estimado_brl"]
    saldo_liquido = round(receita_reciclaveis - custo_transporte, 2)

    resumo_executivo = {
        "modelo_ml_utilizado": previsao_ml["modelo_utilizado"],
        "pontos_avaliados_ml": previsao_ml["quantidade_pontos"],
        "pontos_aprovados_pli": resultado_pli["quantidade_pontos_selecionados"],
        "veiculos_mobilizados_vns": resultado_vns["quantidade_rotas"],
        "peso_total_recolhido_kg": resultado_pli["peso_total_alocado_kg"],
        "impacto_ambiental_co2_evitado_kg": resultado_pli["impacto_ambiental_co2_kg"],
        "receita_bruta_reciclaveis_brl": receita_reciclaveis,
        "custo_operacional_frota_brl": custo_transporte,
        "saldo_operacional_liquido_brl": saldo_liquido,
        "economia_distancia_vns_pct": resultado_vns["percentual_economia_pct"],
    }

    return {
        "data_planejamento": dados.data_planejamento,
        "etapa_1_previsao_ml": {
            "modelo_utilizado": previsao_ml["modelo_utilizado"],
            "quantidade_pontos": previsao_ml["quantidade_pontos"],
            "peso_total_previsto_kg": previsao_ml["peso_total_previsto_kg"],
            "valor_total_estimado_brl": previsao_ml["valor_total_estimado_brl"],
        },
        "etapa_2_selecao_carga_pli": resultado_pli,
        "etapa_3_roteamento_frota_vns": resultado_vns,
        "resumo_executivo": resumo_executivo,
    }
