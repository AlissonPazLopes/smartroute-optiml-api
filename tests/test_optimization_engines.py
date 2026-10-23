"""Testes rigorosos dos motores de otimização: Programação Linear Inteira (PuLP) e Roteamento VNS (CVRP)."""


def test_knapsack_pli_pulp_otimalidade_e_restricoes(client):
    payload = {
        "capacidade_peso_kg": 1000.0,
        "capacidade_volume_m3": 4.0,
        "peso_financeiro": 0.70,
        "peso_ambiental": 0.30,
        "permitir_coleta_parcial_por_material": False,
        "candidatos": [
            {
                "ponto_coleta_id": 1,
                "ponto_nome": "Ponto Baixo Valor",
                "latitude": -23.54,
                "longitude": -46.63,
                "peso_papelao_kg": 600.0,
                "peso_plastico_kg": 100.0,
                "peso_aluminio_kg": 10.0,
                "prioridade_coleta": 2.0,
            },
            {
                "ponto_coleta_id": 2,
                "ponto_nome": "Ponto Alto Valor Alumínio/Plástico",
                "latitude": -23.56,
                "longitude": -46.65,
                "peso_papelao_kg": 200.0,
                "peso_plastico_kg": 220.0,
                "peso_aluminio_kg": 120.0,
                "prioridade_coleta": 9.0,
            },
            {
                "ponto_coleta_id": 3,
                "ponto_nome": "Ponto Médio Alto Valor",
                "latitude": -23.58,
                "longitude": -46.67,
                "peso_papelao_kg": 180.0,
                "peso_plastico_kg": 150.0,
                "peso_aluminio_kg": 80.0,
                "prioridade_coleta": 8.0,
            },
        ],
    }

    res = client.post("/api/otimizacao/alocacao-carga-pli", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status_solver"] == "Optimal"
    assert data["otimo_encontrado"] is True
    assert data["peso_total_alocado_kg"] <= 1000.0
    assert data["volume_total_alocado_m3"] <= 4.0

    ids_escolhidos = {p["ponto_coleta_id"] for p in data["pontos_selecionados"]}
    # Os pontos 2 (540 kg) e 3 (410 kg) somam 950 kg (<= 1000 kg) e têm muito mais valor/prioridade que o ponto 1
    assert ids_escolhidos == {2, 3}
    assert 1 in data["pontos_nao_atendidos_ids"]


def test_roteamento_vns_convergencia_e_economia_distancia(client):
    # Pontos propositalmente embaralhados (zigue-zague norte-sul-leste-oeste) para validar convergência do VNS (N1, N2, N3)
    pontos_embaralhados = [
        {"ponto_coleta_id": 1, "ponto_nome": "Norte 1", "latitude": -23.5010, "longitude": -46.6250, "demanda_kg": 300.0},
        {"ponto_coleta_id": 2, "ponto_nome": "Sul 1", "latitude": -23.6540, "longitude": -46.7090, "demanda_kg": 300.0},
        {"ponto_coleta_id": 3, "ponto_nome": "Norte 2", "latitude": -23.5080, "longitude": -46.6560, "demanda_kg": 300.0},
        {"ponto_coleta_id": 4, "ponto_nome": "Sul 2", "latitude": -23.6460, "longitude": -46.6410, "demanda_kg": 300.0},
        {"ponto_coleta_id": 5, "ponto_nome": "Leste 1", "latitude": -23.5400, "longitude": -46.5760, "demanda_kg": 300.0},
        {"ponto_coleta_id": 6, "ponto_nome": "Oeste 1", "latitude": -23.5610, "longitude": -46.7010, "demanda_kg": 300.0},
        {"ponto_coleta_id": 7, "ponto_nome": "Leste 2", "latitude": -23.5230, "longitude": -46.5410, "demanda_kg": 300.0},
        {"ponto_coleta_id": 8, "ponto_nome": "Oeste 2", "latitude": -23.5280, "longitude": -46.7270, "demanda_kg": 300.0},
    ]

    payload = {
        "deposito": {"nome": "Garagem Central", "latitude": -23.5505, "longitude": -46.6333},
        "max_iteracoes": 60,
        "random_seed": 42,
        "pontos": pontos_embaralhados,
        "veiculos": [
            {
                "id": 1,
                "placa": "SRT1A01",
                "modelo": "Caminhão Compactador 1",
                "capacidade_carga_kg": 1500.0,
                "custo_por_km": 4.50,
            },
            {
                "id": 2,
                "placa": "SRT2B02",
                "modelo": "Caminhão Compactador 2",
                "capacidade_carga_kg": 1500.0,
                "custo_por_km": 4.50,
            },
        ],
    }

    res = client.post("/api/otimizacao/roteamento-vns", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["quantidade_rotas"] == 2
    assert data["distancia_total_otimizada_km"] < data["distancia_rota_nao_otimizada_km"]
    assert data["economia_distancia_km"] > 10.0
    assert data["percentual_economia_pct"] > 15.0
    assert data["custo_total_estimado_brl"] > 0

    todos_ids_visitados = []
    for rota in data["rotas"]:
        assert rota["carga_total_rota_kg"] <= rota["capacidade_veiculo_kg"]
        todos_ids_visitados.extend(rota["sequencia_ids"])
    assert sorted(todos_ids_visitados) == [1, 2, 3, 4, 5, 6, 7, 8]


def test_planejamento_integrado_ml_pli_vns(client):
    # Popular banco e treinar modelo
    seed_res = client.post(
        "/api/seed/gerar-dados",
        json={"dias_historico": 42, "limpar_antes": True, "random_seed": 42},
    )
    assert seed_res.status_code == 201

    plan_res = client.post(
        "/api/otimizacao/planejamento-integrado",
        json={
            "data_planejamento": "2026-10-28",
            "temperatura_media": 27.5,
            "evento_sazonal": False,
            "fator_capacidade_frota": 0.65,
            "max_iteracoes_vns": 50,
            "random_seed": 42,
        },
    )
    assert plan_res.status_code == 200
    plan = plan_res.json()

    assert plan["etapa_1_previsao_ml"]["quantidade_pontos"] == 25
    assert plan["etapa_2_selecao_carga_pli"]["otimo_encontrado"] is True
    assert plan["etapa_2_selecao_carga_pli"]["quantidade_pontos_selecionados"] > 0
    assert plan["etapa_3_roteamento_frota_vns"]["quantidade_rotas"] >= 1
    assert plan["resumo_executivo"]["peso_total_recolhido_kg"] > 0
    assert plan["resumo_executivo"]["receita_bruta_reciclaveis_brl"] > 0
