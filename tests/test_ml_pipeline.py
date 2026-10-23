"""Testes automatizados do pipeline de Machine Learning (Engenharia de Atributos, Treinamento e Previsão)."""


def test_ml_treinar_comparar_e_prever_demanda(client):
    # 1. Popular banco com dados sintéticos realistas
    seed_res = client.post(
        "/api/seed/gerar-dados",
        json={"dias_historico": 42, "limpar_antes": True, "random_seed": 42},
    )
    assert seed_res.status_code == 201

    # 2. Treinar e comparar algoritmos (Multiple Linear Regression vs Random Forest Regressor)
    train_res = client.post(
        "/api/ml/treinar-modelos",
        json={"cv_folds": 4, "n_estimators": 60, "random_state": 42},
    )
    assert train_res.status_code == 200
    train_data = train_res.json()
    assert train_data["sucesso"] is True
    assert train_data["total_amostras"] >= 1000
    assert train_data["melhor_modelo_selecionado"] in (
        "RandomForestRegressor",
        "MultipleLinearRegression",
    )

    # Verificar métricas R², MAE, RMSE e MAPE em ambos os algoritmos
    resumo = train_data["resumo_comparativo"]
    assert resumo["RandomForestRegressor"]["r2_medio"] > 0.85
    assert resumo["MultipleLinearRegression"]["r2_medio"] > 0.80
    assert resumo["RandomForestRegressor"]["mape_medio"] < 15.0

    # 3. Consultar endpoint GET /api/ml/metricas-comparativas
    metricas_res = client.get("/api/ml/metricas-comparativas")
    assert metricas_res.status_code == 200
    metricas_data = metricas_res.json()
    assert "peso_papelao_kg" in metricas_data["metricas_por_alvo"]["RandomForestRegressor"]
    assert "peso_plastico_kg" in metricas_data["metricas_por_alvo"]["RandomForestRegressor"]
    assert "peso_aluminio_kg" in metricas_data["metricas_por_alvo"]["RandomForestRegressor"]
    assert "peso_total_kg" in metricas_data["metricas_por_alvo"]["RandomForestRegressor"]
    assert len(metricas_data["features_utilizadas"]) >= 15

    # 4. Prever demanda para pontos específicos
    prev_res = client.post(
        "/api/ml/prever-demanda",
        json={
            "data_previsao": "2026-10-25",
            "temperatura_media": 28.0,
            "evento_sazonal": True,
            "ponto_ids": [1, 2, 3, 4, 5],
        },
    )
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["quantidade_pontos"] == 5
    assert prev_data["peso_total_previsto_kg"] > 0
    assert prev_data["valor_total_estimado_brl"] > 0
    for item in prev_data["previsoes_por_ponto"]:
        assert item["peso_papelao_kg"] > 0
        assert item["peso_plastico_kg"] > 0
        assert item["peso_aluminio_kg"] > 0
        assert abs(
            item["peso_total_kg"]
            - (item["peso_papelao_kg"] + item["peso_plastico_kg"] + item["peso_aluminio_kg"])
        ) < 0.05


def test_ml_treinar_sem_dados_retorna_400(client):
    res = client.post("/api/ml/treinar-modelos", json={"cv_folds": 3, "n_estimators": 30})
    assert res.status_code == 400
    assert res.json()["sucesso"] is False
