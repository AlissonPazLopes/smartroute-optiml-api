"""Router REST para treinamento, avaliação comparativa e inferência de Machine Learning."""
from typing import Optional

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.ml.model_trainer import ModelTrainerService
from app.schemas.ml import (
    ComparativoModelosResponse,
    PrevisaoDemandaRequest,
    PrevisaoDemandaResponse,
    TreinamentoRequest,
    TreinamentoResponse,
)

router = APIRouter(prefix="/ml", tags=["Machine Learning (Previsão de Demanda)"])


@router.post(
    "/treinar-modelos",
    response_model=TreinamentoResponse,
    status_code=status.HTTP_200_OK,
    summary="Treinar e comparar Multiple Linear Regression e Random Forest Regressor",
)
def treinar_modelos(
    config: Optional[TreinamentoRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    cfg = config if config is not None else TreinamentoRequest()
    trainer = ModelTrainerService(db)
    return trainer.treinar_e_avaliar(
        cv_folds=cfg.cv_folds,
        n_estimators=cfg.n_estimators,
        random_state=cfg.random_state,
    )


@router.get(
    "/metricas-comparativas",
    response_model=ComparativoModelosResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar métricas de validação cruzada (R², MAE, RMSE, MAPE) dos modelos treinados",
)
def obter_metricas_comparativas(db: Session = Depends(get_db)):
    trainer = ModelTrainerService(db)
    return trainer.obter_metricas_comparativas()


@router.post(
    "/prever-demanda",
    response_model=PrevisaoDemandaResponse,
    status_code=status.HTTP_200_OK,
    summary="Prever demanda de coleta seletiva (papelão, plástico, alumínio e total) por ponto",
)
def prever_demanda(
    dados: Optional[PrevisaoDemandaRequest] = Body(default=None),
    db: Session = Depends(get_db),
):
    req = dados if dados is not None else PrevisaoDemandaRequest()
    trainer = ModelTrainerService(db)
    return trainer.prever_demanda_pontos(
        data_previsao=req.data_previsao,
        temperatura_media=req.temperatura_media,
        evento_sazonal=req.evento_sazonal,
        ponto_ids=req.ponto_ids,
        algoritmo_forcado=req.algoritmo,
    )
