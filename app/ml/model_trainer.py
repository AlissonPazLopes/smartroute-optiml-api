"""Treinador, avaliador e preditor de modelos de Machine Learning (Scikit-Learn)."""
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, NotFoundException
from app.ml.feature_engineering import (
    FEATURE_COLUMNS,
    TARGET_COLUMNS,
    construir_features_inferencia,
    extrair_dataset_treinamento,
)
from app.models.ponto_coleta import PontoColeta

ARTIFACTS_DIR = Path("models_artifacts")
MODEL_BUNDLE_PATH = ARTIFACTS_DIR / "smartroute_demand_models.joblib"


def _calcular_metricas(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calcula R², MAE, RMSE e MAPE (%) entre valores reais e preditos."""
    r2 = float(r2_score(y_true, y_pred))
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    denom = np.maximum(np.abs(y_true), 1e-3)
    mape = float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)
    return {
        "r2": round(r2, 4),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 4),
    }


class ModelTrainerService:
    """Serviço responsável pelo treinamento, validação cruzada, persistência e inferência de ML."""

    def __init__(self, db: Session, artifacts_dir: Optional[Path] = None):
        self.db = db
        self.artifacts_dir = artifacts_dir or ARTIFACTS_DIR
        self.bundle_path = self.artifacts_dir / "smartroute_demand_models.joblib"

    def treinar_e_avaliar(self, cv_folds: int = 5, n_estimators: int = 120, random_state: int = 42) -> Dict[str, Any]:
        """
        Treina e compara Multiple Linear Regression e Random Forest Regressor usando validação cruzada
        para cada variável alvo (peso_papelao_kg, peso_plastico_kg, peso_aluminio_kg, peso_total_kg).
        Seleciona automaticamente o melhor modelo e salva os artefatos com joblib.
        """
        X, y = extrair_dataset_treinamento(self.db)
        total_amostras = len(X)

        if total_amostras < 20:
            raise AppException(
                f"Dados insuficientes para treinamento ({total_amostras} registros). "
                "Execute o endpoint /api/seed/gerar-dados antes de treinar.",
                status_code=400,
            )

        kf = KFold(n_splits=min(cv_folds, total_amostras // 4), shuffle=True, random_state=random_state)

        metricas_por_modelo: Dict[str, Dict[str, Dict[str, float]]] = {
            "MultipleLinearRegression": {},
            "RandomForestRegressor": {},
        }
        modelos_finais_vencedores: Dict[str, Any] = {}
        modelos_todos: Dict[str, Dict[str, Any]] = {
            "MultipleLinearRegression": {},
            "RandomForestRegressor": {},
        }
        vencedor_por_alvo: Dict[str, str] = {}

        for target in TARGET_COLUMNS:
            y_target = y[target].to_numpy()

            # 1. Multiple Linear Regression (com padronização)
            pipe_lr = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("regressor", LinearRegression()),
                ]
            )
            preds_lr_cv = cross_val_predict(pipe_lr, X, y_target, cv=kf)
            preds_lr_cv = np.maximum(0.0, preds_lr_cv)
            metricas_lr = _calcular_metricas(y_target, preds_lr_cv)
            pipe_lr.fit(X, y_target)

            # 2. Random Forest Regressor
            rf_model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=14,
                min_samples_leaf=2,
                random_state=random_state,
                n_jobs=-1,
            )
            preds_rf_cv = cross_val_predict(rf_model, X, y_target, cv=kf)
            preds_rf_cv = np.maximum(0.0, preds_rf_cv)
            metricas_rf = _calcular_metricas(y_target, preds_rf_cv)
            rf_model.fit(X, y_target)

            metricas_por_modelo["MultipleLinearRegression"][target] = metricas_lr
            metricas_por_modelo["RandomForestRegressor"][target] = metricas_rf

            modelos_todos["MultipleLinearRegression"][target] = pipe_lr
            modelos_todos["RandomForestRegressor"][target] = rf_model

            if metricas_rf["r2"] >= metricas_lr["r2"]:
                vencedor_por_alvo[target] = "RandomForestRegressor"
                modelos_finais_vencedores[target] = rf_model
            else:
                vencedor_por_alvo[target] = "MultipleLinearRegression"
                modelos_finais_vencedores[target] = pipe_lr

        # Média agregada das métricas por algoritmo
        resumo_algoritmos: Dict[str, Dict[str, float]] = {}
        for alg_name, alvos_dict in metricas_por_modelo.items():
            resumo_algoritmos[alg_name] = {
                "r2_medio": round(float(np.mean([m["r2"] for m in alvos_dict.values()])), 4),
                "mae_medio": round(float(np.mean([m["mae"] for m in alvos_dict.values()])), 4),
                "rmse_medio": round(float(np.mean([m["rmse"] for m in alvos_dict.values()])), 4),
                "mape_medio": round(float(np.mean([m["mape"] for m in alvos_dict.values()])), 4),
            }

        melhor_algoritmo_global = (
            "RandomForestRegressor"
            if resumo_algoritmos["RandomForestRegressor"]["r2_medio"]
            >= resumo_algoritmos["MultipleLinearRegression"]["r2_medio"]
            else "MultipleLinearRegression"
        )

        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        treinado_em = datetime.now(timezone.utc).isoformat()

        bundle = {
            "treinado_em": treinado_em,
            "total_amostras": total_amostras,
            "cv_folds": kf.n_splits,
            "feature_columns": FEATURE_COLUMNS,
            "target_columns": TARGET_COLUMNS,
            "melhor_algoritmo_global": melhor_algoritmo_global,
            "vencedor_por_alvo": vencedor_por_alvo,
            "metricas_detalhadas": metricas_por_modelo,
            "resumo_comparativo": resumo_algoritmos,
            "modelos_vencedores": modelos_finais_vencedores,
            "modelos_todos": modelos_todos,
        }
        joblib.dump(bundle, self.bundle_path)

        return {
            "sucesso": True,
            "mensagem": "Modelos treinados, validados via Cross-Validation e persistidos com sucesso.",
            "treinado_em": treinado_em,
            "total_amostras": total_amostras,
            "cv_folds": kf.n_splits,
            "melhor_modelo_selecionado": melhor_algoritmo_global,
            "vencedor_por_alvo": vencedor_por_alvo,
            "resumo_comparativo": resumo_algoritmos,
            "metricas_por_alvo": metricas_por_modelo,
            "caminho_artefato": str(self.bundle_path),
        }

    def carregar_bundle(self, auto_train_if_missing: bool = False) -> Dict[str, Any]:
        """Carrega o pacote de modelos treinado do disco."""
        if not self.bundle_path.exists():
            if auto_train_if_missing:
                self.treinar_e_avaliar()
            else:
                raise NotFoundException(
                    "Nenhum modelo treinado foi encontrado em disco. Execute POST /api/ml/treinar-modelos primeiro."
                )
        return joblib.load(self.bundle_path)

    def obter_metricas_comparativas(self) -> Dict[str, Any]:
        """Retorna as métricas comparativas completas entre Multiple Linear Regression e Random Forest."""
        bundle = self.carregar_bundle(auto_train_if_missing=False)
        return {
            "treinado_em": bundle["treinado_em"],
            "total_amostras": bundle["total_amostras"],
            "cv_folds": bundle["cv_folds"],
            "melhor_modelo_selecionado": bundle["melhor_algoritmo_global"],
            "vencedor_por_alvo": bundle["vencedor_por_alvo"],
            "resumo_comparativo": bundle["resumo_comparativo"],
            "metricas_por_alvo": bundle["metricas_detalhadas"],
            "features_utilizadas": bundle["feature_columns"],
        }

    def prever_demanda_pontos(
        self,
        data_previsao: date,
        temperatura_media: float = 25.0,
        evento_sazonal: bool = False,
        ponto_ids: Optional[List[int]] = None,
        algoritmo_forcado: Optional[str] = None,
        auto_train_if_missing: bool = True,
    ) -> Dict[str, Any]:
        """
        Realiza a previsão de peso (papelão, plástico, alumínio e total) e valor estimado
        para os pontos de coleta solicitados (ou todos os pontos ativos).
        """
        bundle = self.carregar_bundle(auto_train_if_missing=auto_train_if_missing)

        query = self.db.query(PontoColeta).filter(PontoColeta.ativo == True)  # noqa: E712
        if ponto_ids:
            query = query.filter(PontoColeta.id.in_(ponto_ids))
        pontos = query.order_by(PontoColeta.id.asc()).all()

        if not pontos:
            raise NotFoundException("Nenhum ponto de coleta ativo encontrado para os IDs informados.")

        X_inf = construir_features_inferencia(
            pontos=pontos,
            data_previsao=data_previsao,
            temperatura_media=temperatura_media,
            evento_sazonal=evento_sazonal,
        )

        if algoritmo_forcado and algoritmo_forcado in bundle["modelos_todos"]:
            modelos_uso = bundle["modelos_todos"][algoritmo_forcado]
            modelo_nome_usado = algoritmo_forcado
        else:
            modelos_uso = bundle["modelos_vencedores"]
            modelo_nome_usado = bundle["melhor_algoritmo_global"]

        pred_papelao = np.maximum(1.0, modelos_uso["peso_papelao_kg"].predict(X_inf))
        pred_plastico = np.maximum(1.0, modelos_uso["peso_plastico_kg"].predict(X_inf))
        pred_aluminio = np.maximum(0.5, modelos_uso["peso_aluminio_kg"].predict(X_inf))

        previsoes_lista: List[Dict[str, Any]] = []
        peso_total_global = 0.0
        valor_total_global = 0.0

        for idx, ponto in enumerate(pontos):
            p_pap = round(float(pred_papelao[idx]), 2)
            p_pla = round(float(pred_plastico[idx]), 2)
            p_alu = round(float(pred_aluminio[idx]), 2)
            p_tot = round(p_pap + p_pla + p_alu, 2)
            val_brl = round(p_pap * 0.85 + p_pla * 2.40 + p_alu * 7.50, 2)

            ocupacao_pct = round(min(100.0, (p_tot / max(ponto.capacidade_armazenamento_kg, 1.0)) * 100.0), 2)
            prioridade = round(min(10.0, max(1.0, (p_tot / 100.0) + (ocupacao_pct / 20.0))), 2)

            previsoes_lista.append(
                {
                    "ponto_coleta_id": ponto.id,
                    "ponto_nome": ponto.nome,
                    "bairro": ponto.bairro,
                    "tipo_zona": ponto.tipo_zona,
                    "latitude": ponto.latitude,
                    "longitude": ponto.longitude,
                    "peso_papelao_kg": p_pap,
                    "peso_plastico_kg": p_pla,
                    "peso_aluminio_kg": p_alu,
                    "peso_total_kg": p_tot,
                    "valor_estimado_brl": val_brl,
                    "taxa_ocupacao_estimada_pct": ocupacao_pct,
                    "prioridade_coleta": prioridade,
                }
            )
            peso_total_global += p_tot
            valor_total_global += val_brl

        return {
            "data_previsao": data_previsao,
            "dia_semana": data_previsao.weekday(),
            "temperatura_media": temperatura_media,
            "evento_sazonal": evento_sazonal,
            "modelo_utilizado": modelo_nome_usado,
            "quantidade_pontos": len(previsoes_lista),
            "peso_total_previsto_kg": round(peso_total_global, 2),
            "valor_total_estimado_brl": round(valor_total_global, 2),
            "previsoes_por_ponto": previsoes_lista,
        }
