"""
Teste Ponta a Ponta (E2E) do fluxo completo da plataforma SmartRoute OptiML API:
Autenticação JWT -> Data Seeder -> Cadastro Operacional -> Treinamento e Inferência ML ->
Otimização de Carga via PLI (PuLP) -> Roteirização de Frota via Meta-heurística VNS.
"""
from scripts.run_benchmarks import gerar_cenario_sintetico_pontos, gerar_frota_escalonada


def test_fluxo_e2e_completo_smartroute_optiml(client):
    # 1. Health Check da API
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"

    # 2. Registro e Login de Gestor Logístico (OAuth2 / JWT)
    reg_res = client.post(
        "/api/auth/registro",
        json={
            "nome": "Gestor E2E SmartRoute",
            "email": "gestor.e2e@smartroute.com",
            "senha": "StrongPassword!2026",
            "perfil": "GESTOR",
        },
    )
    assert reg_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"email": "gestor.e2e@smartroute.com", "senha": "StrongPassword!2026"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Popular base de dados sintética realista (25 pontos, 6 veículos, >1000 históricos)
    seed_res = client.post(
        "/api/seed/gerar-dados",
        json={"dias_historico": 44, "limpar_antes": True, "random_seed": 101},
    )
    assert seed_res.status_code == 201
    seed_body = seed_res.json()
    assert seed_body["pontos_coleta_criados"] == 25
    assert seed_body["veiculos_criados"] == 6
    assert seed_body["historicos_criados"] == 1100

    # 4. Adicionar 1 novo ponto de coleta estratégico e 1 novo caminhão via endpoints autenticados
    novo_ponto_res = client.post(
        "/api/pontos-coleta",
        headers=headers,
        json={
            "nome": "Ecoponto Estratégico Paulista",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "latitude": -23.5632,
            "longitude": -46.6544,
            "populacao_atendida": 61000,
            "tipo_zona": "COMERCIAL",
            "capacidade_armazenamento_kg": 3500.0,
            "ativo": True,
        },
    )
    assert novo_ponto_res.status_code == 201

    novo_veic_res = client.post(
        "/api/veiculos-frota",
        headers=headers,
        json={
            "placa": "SRT9Z99",
            "modelo": "Scania P280 Compactador Alta Capacidade",
            "capacidade_carga_kg": 11000.0,
            "volume_maximo_m3": 32.0,
            "custo_por_km": 6.40,
            "disponivel": True,
        },
    )
    assert novo_veic_res.status_code == 201

    # 5. Treinar modelos de Machine Learning e validar métricas comparativas
    ml_train_res = client.post(
        "/api/ml/treinar-modelos",
        json={"cv_folds": 4, "n_estimators": 60, "random_state": 42},
    )
    assert ml_train_res.status_code == 200
    assert ml_train_res.json()["sucesso"] is True

    comp_res = client.get("/api/ml/metricas-comparativas")
    assert comp_res.status_code == 200
    comp_body = comp_res.json()
    assert comp_body["resumo_comparativo"]["RandomForestRegressor"]["r2_medio"] > 0.85
    assert comp_body["resumo_comparativo"]["MultipleLinearRegression"]["r2_medio"] > 0.80

    # 6. Executar Planejamento Integrado (ML -> PLI PuLP -> VNS CVRP)
    plan_res = client.post(
        "/api/otimizacao/planejamento-integrado",
        json={
            "data_planejamento": "2026-11-05",
            "temperatura_media": 29.0,
            "evento_sazonal": True,
            "fator_capacidade_frota": 0.70,
            "max_iteracoes_vns": 60,
            "random_seed": 42,
        },
    )
    assert plan_res.status_code == 200
    plan = plan_res.json()

    assert plan["etapa_1_previsao_ml"]["quantidade_pontos"] == 26
    assert plan["etapa_2_selecao_carga_pli"]["status_solver"] == "Optimal"
    assert plan["etapa_2_selecao_carga_pli"]["ocupacao_peso_pct"] <= 100.0
    assert plan["etapa_2_selecao_carga_pli"]["ocupacao_volume_pct"] <= 100.0

    vns_stage = plan["etapa_3_roteamento_frota_vns"]
    assert vns_stage["quantidade_rotas"] >= 1
    assert vns_stage["distancia_total_otimizada_km"] <= vns_stage["distancia_rota_nao_otimizada_km"]

    exec_summary = plan["resumo_executivo"]
    assert exec_summary["receita_bruta_reciclaveis_brl"] > 0
    assert exec_summary["impacto_ambiental_co2_evitado_kg"] > 0


def test_geradores_cenario_benchmark():
    pontos_20 = gerar_cenario_sintetico_pontos(20, seed=42)
    frota_20 = gerar_frota_escalonada(20)
    assert len(pontos_20) == 20
    assert len(frota_20) >= 3
    assert all(p["demanda_kg"] > 0 for p in pontos_20)
