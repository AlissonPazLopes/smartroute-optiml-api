def test_crud_completo_ponto_coleta(client, auth_headers):
    # 1. Criar Ponto de Coleta
    payload = {
        "nome": "Ecoponto Central Sé",
        "bairro": "Sé",
        "cidade": "São Paulo",
        "latitude": -23.5505,
        "longitude": -46.6333,
        "populacao_atendida": 45000,
        "tipo_zona": "COMERCIAL",
        "capacidade_armazenamento_kg": 3000.0,
        "ativo": True,
    }
    create_res = client.post("/api/pontos-coleta", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    ponto = create_res.json()
    ponto_id = ponto["id"]
    assert ponto["nome"] == "Ecoponto Central Sé"

    # 2. Listar com filtro e paginação
    list_res = client.get("/api/pontos-coleta?page=1&size=10&tipo_zona=COMERCIAL")
    assert list_res.status_code == 200
    paginated = list_res.json()
    assert paginated["total"] == 1
    assert len(paginated["items"]) == 1

    # 3. Atualizar Ponto
    update_res = client.put(
        f"/api/pontos-coleta/{ponto_id}",
        json={"capacidade_armazenamento_kg": 3500.0, "populacao_atendida": 48000},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["capacidade_armazenamento_kg"] == 3500.0

    # 4. Criar Histórico associado ao Ponto
    hist_payload = {
        "ponto_coleta_id": ponto_id,
        "data_coleta": "2026-10-20",
        "temperatura_media": 26.5,
        "evento_sazonal": False,
        "peso_papelao_kg": 180.0,
        "peso_plastico_kg": 110.0,
        "peso_aluminio_kg": 35.0,
    }
    hist_res = client.post("/api/historicos-coleta", json=hist_payload, headers=auth_headers)
    assert hist_res.status_code == 201
    hist_data = hist_res.json()
    assert hist_data["peso_total_kg"] == 325.0
    assert hist_data["valor_estimado_brl"] > 0

    # 5. Remover Ponto
    del_res = client.delete(f"/api/pontos-coleta/{ponto_id}", headers=auth_headers)
    assert del_res.status_code == 204

    get_res = client.get(f"/api/pontos-coleta/{ponto_id}")
    assert get_res.status_code == 404


def test_validacao_pydantic_ponto_coleta_invalido(client, auth_headers):
    payload_invalido = {
        "nome": "Ponto Inválido",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "latitude": -125.0,  # Inválido (< -90)
        "longitude": -46.63,
        "populacao_atendida": -500,  # Inválido (<= 0)
        "tipo_zona": "ZONA_DESCONHECIDA",
        "capacidade_armazenamento_kg": 1000.0,
    }
    res = client.post("/api/pontos-coleta", json=payload_invalido, headers=auth_headers)
    assert res.status_code == 422
    body = res.json()
    assert body["sucesso"] is False
    assert body["erro"] == "ValidationError"


def test_crud_completo_veiculo_frota_e_validacao_placa(client, auth_headers):
    veiculo_payload = {
        "placa": "ABC-1D23",
        "modelo": "Mercedes-Benz Atego Compactador",
        "capacidade_carga_kg": 6500.0,
        "volume_maximo_m3": 18.5,
        "custo_por_km": 5.25,
        "disponivel": True,
    }
    create_res = client.post("/api/veiculos-frota", json=veiculo_payload, headers=auth_headers)
    assert create_res.status_code == 201
    veiculo = create_res.json()
    assert veiculo["placa"] == "ABC1D23"
    veiculo_id = veiculo["id"]

    # Placa inválida deve retornar 422
    placa_invalida_res = client.post(
        "/api/veiculos-frota",
        json={**veiculo_payload, "placa": "123-ABCD"},
        headers=auth_headers,
    )
    assert placa_invalida_res.status_code == 422

    # Atualizar disponibilidade
    upd_res = client.put(
        f"/api/veiculos-frota/{veiculo_id}",
        json={"disponivel": False},
        headers=auth_headers,
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["disponivel"] is False

    # Deletar veículo
    del_res = client.delete(f"/api/veiculos-frota/{veiculo_id}", headers=auth_headers)
    assert del_res.status_code == 204
