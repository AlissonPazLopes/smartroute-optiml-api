def test_registrar_usuario_sucesso(client):
    payload = {
        "nome": "Alisson Gestor",
        "email": "alisson@smartroute.com",
        "senha": "Password123!",
        "perfil": "GESTOR",
    }
    response = client.post("/api/auth/registro", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alisson@smartroute.com"
    assert data["nome"] == "Alisson Gestor"
    assert data["perfil"] == "GESTOR"
    assert data["ativo"] is True
    assert "id" in data


def test_registrar_email_duplicado_retorna_409(client):
    payload = {
        "nome": "Usuário 1",
        "email": "duplicado@smartroute.com",
        "senha": "Password123!",
        "perfil": "OPERADOR",
    }
    res1 = client.post("/api/auth/registro", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/registro", json=payload)
    assert res2.status_code == 409
    err = res2.json()
    assert err["sucesso"] is False
    assert "duplicado@smartroute.com" in err["mensagem"]


def test_login_json_e_acesso_rota_protegida(client):
    client.post(
        "/api/auth/registro",
        json={
            "nome": "Analista ML",
            "email": "analista@smartroute.com",
            "senha": "mlpassword123",
            "perfil": "ANALISTA",
        },
    )

    login_res = client.post(
        "/api/auth/login",
        json={"email": "analista@smartroute.com", "senha": "mlpassword123"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "analista@smartroute.com"


def test_login_oauth2_form_data(client):
    client.post(
        "/api/auth/registro",
        json={
            "nome": "Form User",
            "email": "form@smartroute.com",
            "senha": "formpassword123",
            "perfil": "OPERADOR",
        },
    )
    res = client.post(
        "/api/auth/login",
        data={"username": "form@smartroute.com", "password": "formpassword123"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_senha_incorreta_retorna_401(client):
    client.post(
        "/api/auth/registro",
        json={
            "nome": "Teste Erro",
            "email": "erro@smartroute.com",
            "senha": "senhaCorreta123",
            "perfil": "OPERADOR",
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"email": "erro@smartroute.com", "senha": "senhaErrada999"},
    )
    assert res.status_code == 401
    assert res.json()["sucesso"] is False


def test_acesso_sem_token_retorna_401(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
