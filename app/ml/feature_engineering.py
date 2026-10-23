"""Módulo de pré-processamento e engenharia de atributos para previsão de demanda de recicláveis."""
from datetime import date
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.historico_coleta import HistoricoColeta
from app.models.ponto_coleta import PontoColeta

FEATURE_COLUMNS: List[str] = [
    "populacao_atendida",
    "capacidade_armazenamento_kg",
    "latitude",
    "longitude",
    "dia_semana",
    "dia_semana_sin",
    "dia_semana_cos",
    "eh_fim_de_semana",
    "temperatura_media",
    "indice_calor_bebidas",
    "evento_sazonal",
    "zona_COMERCIAL",
    "zona_RESIDENCIAL",
    "zona_INDUSTRIAL",
    "zona_MISTA",
    "pop_x_sazonal",
    "pop_x_fds",
    "pop_x_comercial",
    "pop_x_residencial",
    "pop_x_industrial",
    "pop_x_temp_bebidas",
]

TARGET_COLUMNS: List[str] = [
    "peso_papelao_kg",
    "peso_plastico_kg",
    "peso_aluminio_kg",
    "peso_total_kg",
]


def _transform_raw_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica transformações matemáticas, codificação cíclica, one-hot e termos de interação."""
    out = pd.DataFrame(index=df.index)

    pop_mil = df["populacao_atendida"].astype(float) / 1000.0
    out["populacao_atendida"] = df["populacao_atendida"].astype(float)
    out["capacidade_armazenamento_kg"] = df["capacidade_armazenamento_kg"].astype(float)
    out["latitude"] = df["latitude"].astype(float)
    out["longitude"] = df["longitude"].astype(float)

    dia_semana = df["dia_semana"].astype(int)
    out["dia_semana"] = dia_semana.astype(float)
    out["dia_semana_sin"] = np.sin(2.0 * np.pi * dia_semana / 7.0)
    out["dia_semana_cos"] = np.cos(2.0 * np.pi * dia_semana / 7.0)

    eh_fds = dia_semana.isin([5, 6]).astype(float)
    out["eh_fim_de_semana"] = eh_fds

    temp = df["temperatura_media"].astype(float)
    out["temperatura_media"] = temp
    calor_bebidas = np.maximum(0.0, temp - 20.0)
    out["indice_calor_bebidas"] = calor_bebidas

    sazonal = df["evento_sazonal"].astype(float)
    out["evento_sazonal"] = sazonal

    zona_upper = df["tipo_zona"].astype(str).str.strip().str.upper()
    out["zona_COMERCIAL"] = (zona_upper == "COMERCIAL").astype(float)
    out["zona_RESIDENCIAL"] = (zona_upper == "RESIDENCIAL").astype(float)
    out["zona_INDUSTRIAL"] = (zona_upper == "INDUSTRIAL").astype(float)
    out["zona_MISTA"] = (zona_upper == "MISTA").astype(float)

    # Termos de interação física/demográfica
    out["pop_x_sazonal"] = pop_mil * sazonal
    out["pop_x_fds"] = pop_mil * eh_fds
    out["pop_x_comercial"] = pop_mil * out["zona_COMERCIAL"]
    out["pop_x_residencial"] = pop_mil * out["zona_RESIDENCIAL"]
    out["pop_x_industrial"] = pop_mil * out["zona_INDUSTRIAL"]
    out["pop_x_temp_bebidas"] = pop_mil * calor_bebidas

    return out[FEATURE_COLUMNS]


def extrair_dataset_treinamento(db: Session) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extrai os registros de HistoricoColeta combinados com PontoColeta a partir do banco de dados
    e retorna as matrizes (X, y) prontas para treinamento e validação cruzada.
    """
    registros = (
        db.query(
            HistoricoColeta.dia_semana,
            HistoricoColeta.temperatura_media,
            HistoricoColeta.evento_sazonal,
            HistoricoColeta.peso_papelao_kg,
            HistoricoColeta.peso_plastico_kg,
            HistoricoColeta.peso_aluminio_kg,
            HistoricoColeta.peso_total_kg,
            PontoColeta.populacao_atendida,
            PontoColeta.capacidade_armazenamento_kg,
            PontoColeta.latitude,
            PontoColeta.longitude,
            PontoColeta.tipo_zona,
        )
        .join(PontoColeta, HistoricoColeta.ponto_coleta_id == PontoColeta.id)
        .all()
    )

    if not registros:
        return pd.DataFrame(columns=FEATURE_COLUMNS), pd.DataFrame(columns=TARGET_COLUMNS)

    rows: List[Dict] = []
    for r in registros:
        rows.append(
            {
                "dia_semana": r.dia_semana,
                "temperatura_media": r.temperatura_media,
                "evento_sazonal": int(bool(r.evento_sazonal)),
                "peso_papelao_kg": r.peso_papelao_kg,
                "peso_plastico_kg": r.peso_plastico_kg,
                "peso_aluminio_kg": r.peso_aluminio_kg,
                "peso_total_kg": r.peso_total_kg,
                "populacao_atendida": r.populacao_atendida,
                "capacidade_armazenamento_kg": r.capacidade_armazenamento_kg,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "tipo_zona": r.tipo_zona,
            }
        )

    df_raw = pd.DataFrame(rows)
    X = _transform_raw_dataframe(df_raw)
    y = df_raw[TARGET_COLUMNS].astype(float)
    return X, y


def construir_features_inferencia(
    pontos: List[PontoColeta],
    data_previsao: date,
    temperatura_media: float,
    evento_sazonal: bool,
) -> pd.DataFrame:
    """
    Constrói o DataFrame de atributos engenheirados para um conjunto de pontos de coleta
    em uma data futura específica.
    """
    dia_semana = data_previsao.weekday()
    rows: List[Dict] = []
    for p in pontos:
        rows.append(
            {
                "populacao_atendida": p.populacao_atendida,
                "capacidade_armazenamento_kg": p.capacidade_armazenamento_kg,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "tipo_zona": p.tipo_zona,
                "dia_semana": dia_semana,
                "temperatura_media": temperatura_media,
                "evento_sazonal": int(bool(evento_sazonal)),
            }
        )
    df_raw = pd.DataFrame(rows)
    return _transform_raw_dataframe(df_raw)
