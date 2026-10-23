def test_seeder_gera_25_pontos_6_veiculos_e_mais_de_1000_historicos(client):
    res = client.post(
        "/api/seed/gerar-dados",
        json={"dias_historico": 45, "limpar_antes": True, "random_seed": 42},
    )
    assert res.status_code == 201
    data = res.json()

    assert data["sucesso"] is True
    assert data["pontos_coleta_criados"] == 25
    assert data["veiculos_criados"] == 6
    assert data["historicos_criados"] >= 1000
    assert data["historicos_criados"] == 1125  # 25 pontos * 45 dias
    # Verifica que há correlação positiva real entre população atendida e peso coletado
    assert data["correlacao_populacao_peso"] > 0.65

    # Verificar listagem via endpoints REST
    pontos_res = client.get("/api/pontos-coleta?page=1&size=50")
    assert pontos_res.status_code == 200
    assert pontos_res.json()["total"] == 25

    veiculos_res = client.get("/api/veiculos-frota?page=1&size=20")
    assert veiculos_res.status_code == 200
    assert veiculos_res.json()["total"] == 6

    hist_res = client.get("/api/historicos-coleta?page=1&size=25")
    assert hist_res.status_code == 200
    assert hist_res.json()["total"] == 1125
    primeiro_item = hist_res.json()["items"][0]
    assert primeiro_item["peso_total_kg"] > 0
    assert primeiro_item["valor_estimado_brl"] > 0
