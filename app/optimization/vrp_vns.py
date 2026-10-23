"""
Motor de Roteamento de Veículos Capacitado (CVRP) utilizando Meta-heurística
Variable Neighborhood Search (VNS) com Busca Local Variable Neighborhood Descent (VND)
e cálculo geodésico de matriz de distâncias Haversine.
"""
import copy
import math
import random
from typing import Any, Dict, List, Tuple

import numpy as np

RAIO_TERRA_KM = 6371.0088


def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula a distância geodésica Haversine (em km) entre duas coordenadas (latitude, longitude)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(d_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return RAIO_TERRA_KM * c


def construir_matriz_distancias_haversine(nos: List[Dict[str, Any]]) -> np.ndarray:
    """
    Constrói a matriz simétrica N x N de distâncias Haversine (em km).
    O índice 0 representa a Garagem/Central de Triagem (Depósito), e 1..N-1 representam os pontos de coleta.
    """
    n = len(nos)
    matriz = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            dist = calcular_distancia_haversine(
                float(nos[i]["latitude"]),
                float(nos[i]["longitude"]),
                float(nos[j]["latitude"]),
                float(nos[j]["longitude"]),
            )
            matriz[i, j] = dist
            matriz[j, i] = dist
    return matriz


def calcular_distancia_rota(rota: List[int], matriz_dist: np.ndarray) -> float:
    """Calcula a distância total (em km) de uma rota saindo do depósito (0), visitando os nós em `rota` e retornando a (0)."""
    if not rota:
        return 0.0
    dist_total = float(matriz_dist[0, rota[0]])
    for k in range(len(rota) - 1):
        dist_total += float(matriz_dist[rota[k], rota[k + 1]])
    dist_total += float(matriz_dist[rota[-1], 0])
    return dist_total


def calcular_distancia_solucao(rotas: List[List[int]], matriz_dist: np.ndarray) -> float:
    """Soma a distância total de todas as rotas da frota."""
    return sum(calcular_distancia_rota(r, matriz_dist) for r in rotas if r)


def construir_solucao_ingenua_sequencial(
    demandas_kg: List[float],
    capacidades_veiculos_kg: List[float],
) -> List[List[int]]:
    """
    Gera a rota inicial não otimizada (na ordem original de entrada dos pontos),
    respeitando apenas a capacidade dos veículos, para servir de baseline de comparação.
    """
    num_clientes = len(demandas_kg) - 1
    rotas: List[List[int]] = [[] for _ in capacidades_veiculos_kg]
    cargas: List[float] = [0.0 for _ in capacidades_veiculos_kg]

    v_idx = 0
    for cliente_node in range(1, num_clientes + 1):
        dem = demandas_kg[cliente_node]
        alocado = False
        for tent in range(len(capacidades_veiculos_kg)):
            idx = (v_idx + tent) % len(capacidades_veiculos_kg)
            if cargas[idx] + dem <= capacidades_veiculos_kg[idx]:
                rotas[idx].append(cliente_node)
                cargas[idx] += dem
                v_idx = idx
                alocado = True
                break
        if not alocado:
            # Aloca no veículo com maior folga residual
            idx_maior_folga = max(
                range(len(capacidades_veiculos_kg)),
                key=lambda k: capacidades_veiculos_kg[k] - cargas[k],
            )
            rotas[idx_maior_folga].append(cliente_node)
            cargas[idx_maior_folga] += dem

    return [r for r in rotas if r]


def construir_solucao_gulosa_nearest_neighbor(
    matriz_dist: np.ndarray,
    demandas_kg: List[float],
    capacidades_veiculos_kg: List[float],
) -> List[List[int]]:
    """
    Heurística construtiva gulosa (Nearest Neighbor) para o CVRP:
    Para cada veículo disponível, parte do depósito (0) e adiciona iterativamente o ponto não visitado
    mais próximo que caiba na capacidade residual do veículo.
    """
    nao_visitados = set(range(1, len(demandas_kg)))
    rotas: List[List[int]] = []

    for cap_veiculo in capacidades_veiculos_kg:
        if not nao_visitados:
            break
        rota_atual: List[int] = []
        carga_atual = 0.0
        no_atual = 0

        while nao_visitados:
            candidatos_viaveis = [
                c for c in nao_visitados if carga_atual + demandas_kg[c] <= cap_veiculo
            ]
            if not candidatos_viaveis:
                break
            proximo_no = min(candidatos_viaveis, key=lambda c: float(matriz_dist[no_atual, c]))
            rota_atual.append(proximo_no)
            carga_atual += demandas_kg[proximo_no]
            nao_visitados.remove(proximo_no)
            no_atual = proximo_no

        if rota_atual:
            rotas.append(rota_atual)

    # Caso algum cliente exceda a capacidade nominal isolada, insere na rota de menor impacto
    while nao_visitados:
        c = nao_visitados.pop()
        if not rotas:
            rotas.append([c])
        else:
            melhor_r = min(
                range(len(rotas)),
                key=lambda r_idx: matriz_dist[rotas[r_idx][-1], c],
            )
            rotas[melhor_r].append(c)

    return rotas


def vizinhanca_n1_swap_intra_rota(rota: List[int], matriz_dist: np.ndarray) -> Tuple[List[int], bool]:
    """
    Estrutura de Vizinhança N1 (Swap intra-rota):
    Testa a troca de posição entre todos os pares de pontos dentro da mesma rota
    e aplica o melhor movimento de melhoria (Best Improvement).
    """
    n = len(rota)
    if n < 2:
        return rota, False

    melhor_rota = rota
    melhor_dist = calcular_distancia_rota(rota, matriz_dist)
    melhorou = False

    for i in range(n - 1):
        for j in range(i + 1, n):
            nova = rota[:]
            nova[i], nova[j] = nova[j], nova[i]
            d = calcular_distancia_rota(nova, matriz_dist)
            if d + 1e-6 < melhor_dist:
                melhor_dist = d
                melhor_rota = nova
                melhorou = True

    return melhor_rota, melhorou


def vizinhanca_n2_two_opt(rota: List[int], matriz_dist: np.ndarray) -> Tuple[List[int], bool]:
    """
    Estrutura de Vizinhança N2 (2-Opt):
    Inverte segmentos contíguos da rota para eliminar cruzamentos de arestas.
    """
    n = len(rota)
    if n < 3:
        return rota, False

    melhor_rota = rota
    melhor_dist = calcular_distancia_rota(rota, matriz_dist)
    melhorou = False

    for i in range(n - 1):
        for j in range(i + 1, n):
            nova = rota[:i] + list(reversed(rota[i : j + 1])) + rota[j + 1 :]
            d = calcular_distancia_rota(nova, matriz_dist)
            if d + 1e-6 < melhor_dist:
                melhor_dist = d
                melhor_rota = nova
                melhorou = True

    return melhor_rota, melhorou


def vizinhanca_n3_relocate(
    rotas: List[List[int]],
    matriz_dist: np.ndarray,
    demandas_kg: List[float],
    capacidades_veiculos_kg: List[float],
) -> Tuple[List[List[int]], bool]:
    """
    Estrutura de Vizinhança N3 (Relocate inter-rotas e intra-rota):
    Realoca um ponto de coleta de sua posição atual para a melhor posição em outra rota
    (respeitando capacidade) ou na própria rota.
    """
    melhor_rotas = [r[:] for r in rotas]
    melhor_dist = calcular_distancia_solucao(melhor_rotas, matriz_dist)
    melhorou = False

    cargas_atuais = [sum(demandas_kg[no] for no in r) for r in melhor_rotas]

    for r_orig in range(len(melhor_rotas)):
        rota_o = melhor_rotas[r_orig]
        for pos_orig in range(len(rota_o)):
            cliente = rota_o[pos_orig]
            dem_c = demandas_kg[cliente]

            for r_dest in range(len(melhor_rotas)):
                cap_dest = (
                    capacidades_veiculos_kg[r_dest]
                    if r_dest < len(capacidades_veiculos_kg)
                    else capacidades_veiculos_kg[-1]
                )
                if r_orig != r_dest and (cargas_atuais[r_dest] + dem_c > cap_dest):
                    continue

                for pos_dest in range(len(melhor_rotas[r_dest]) + 1):
                    if r_orig == r_dest and (pos_dest == pos_orig or pos_dest == pos_orig + 1):
                        continue

                    candidatas = [r[:] for r in melhor_rotas]
                    no_removido = candidatas[r_orig].pop(pos_orig)
                    insert_idx = pos_dest if (r_orig != r_dest or pos_dest < pos_orig) else pos_dest - 1
                    candidatas[r_dest].insert(insert_idx, no_removido)

                    dist_cand = calcular_distancia_solucao(candidatas, matriz_dist)
                    if dist_cand + 1e-6 < melhor_dist:
                        return [r for r in candidatas if r], True

    return melhor_rotas, melhorou


def busca_local_vnd(
    rotas: List[List[int]],
    matriz_dist: np.ndarray,
    demandas_kg: List[float],
    capacidades_veiculos_kg: List[float],
) -> List[List[int]]:
    """
    Variable Neighborhood Descent (VND):
    Explora sistematicamente as vizinhanças N1 (Swap), N2 (2-Opt) e N3 (Relocate)
    até atingir um ótimo local em todas as três estruturas.
    """
    atual = [r[:] for r in rotas if r]
    k = 1
    while k <= 3:
        melhorou_global = False
        if k == 1:
            for idx in range(len(atual)):
                nova_r, melhorou = vizinhanca_n1_swap_intra_rota(atual[idx], matriz_dist)
                if melhorou:
                    atual[idx] = nova_r
                    melhorou_global = True
        elif k == 2:
            for idx in range(len(atual)):
                nova_r, melhorou = vizinhanca_n2_two_opt(atual[idx], matriz_dist)
                if melhorou:
                    atual[idx] = nova_r
                    melhorou_global = True
        elif k == 3:
            nova_sol, melhorou = vizinhanca_n3_relocate(
                atual, matriz_dist, demandas_kg, capacidades_veiculos_kg
            )
            if melhorou:
                atual = nova_sol
                melhorou_global = True

        if melhorou_global:
            k = 1
        else:
            k += 1

    return [r for r in atual if r]


def perturbar_solucao_shaking(
    rotas: List[List[int]],
    nivel_k: int,
    demandas_kg: List[float],
    capacidades_veiculos_kg: List[float],
    rng: random.Random,
) -> List[List[int]]:
    """
    Fase de Shaking (Perturbação Estocástica) do VNS para escapar de ótimos locais:
    - k = 1: Swap aleatório intra-rota
    - k = 2: Inversão aleatória 2-Opt de sub-segmento
    - k = 3: Troca/realocação aleatória entre rotas viáveis
    """
    copia = [r[:] for r in rotas if r]
    if not copia:
        return copia

    if nivel_k == 1:
        rotas_validas = [r for r in copia if len(r) >= 2]
        if rotas_validas:
            r = rng.choice(rotas_validas)
            i, j = rng.sample(range(len(r)), 2)
            r[i], r[j] = r[j], r[i]

    elif nivel_k == 2:
        rotas_validas = [r for r in copia if len(r) >= 3]
        if rotas_validas:
            r = rng.choice(rotas_validas)
            i, j = sorted(rng.sample(range(len(r)), 2))
            r[i : j + 1] = reversed(r[i : j + 1])

    elif nivel_k >= 3:
        if len(copia) >= 2:
            r1_idx, r2_idx = rng.sample(range(len(copia)), 2)
            if copia[r1_idx]:
                pos = rng.randrange(len(copia[r1_idx]))
                cliente = copia[r1_idx][pos]
                carga_r2 = sum(demandas_kg[n] for n in copia[r2_idx])
                cap_r2 = (
                    capacidades_veiculos_kg[r2_idx]
                    if r2_idx < len(capacidades_veiculos_kg)
                    else capacidades_veiculos_kg[-1]
                )
                if carga_r2 + demandas_kg[cliente] <= cap_r2:
                    copia[r1_idx].pop(pos)
                    insert_pos = rng.randrange(len(copia[r2_idx]) + 1)
                    copia[r2_idx].insert(insert_pos, cliente)
        elif len(copia[0]) >= 2:
            r = copia[0]
            i, j = rng.sample(range(len(r)), 2)
            r[i], r[j] = r[j], r[i]

    return [r for r in copia if r]


def executar_roteamento_vns(
    deposito: Dict[str, Any],
    pontos: List[Dict[str, Any]],
    veiculos: List[Dict[str, Any]],
    max_iteracoes: int = 80,
    random_seed: int = 42,
) -> Dict[str, Any]:
    """
    Executa a meta-heurística completa Variable Neighborhood Search (VNS) para o CVRP.
    Retorna as rotas otimizadas por veículo, distância total (km), custo operacional (R$)
    e o percentual de economia em relação à rota inicial não otimizada.
    """
    if not pontos:
        return {
            "algoritmo": "Variable Neighborhood Search (VNS + VND)",
            "max_iteracoes": max_iteracoes,
            "distancia_rota_nao_otimizada_km": 0.0,
            "distancia_total_otimizada_km": 0.0,
            "economia_distancia_km": 0.0,
            "percentual_economia_pct": 0.0,
            "custo_total_estimado_brl": 0.0,
            "quantidade_rotas": 0,
            "rotas": [],
        }

    rng = random.Random(random_seed)

    # Ordena veículos por maior eficiência (capacidade / custo_por_km)
    veiculos_ordenados = sorted(
        veiculos,
        key=lambda v: float(v.get("capacidade_carga_kg", 5000.0)) / max(float(v.get("custo_por_km", 4.5)), 0.1),
        reverse=True,
    )

    nos: List[Dict[str, Any]] = [
        {
            "ponto_coleta_id": 0,
            "ponto_nome": deposito.get("nome", "Central de Triagem SmartRoute (Depósito)"),
            "latitude": float(deposito.get("latitude", -23.5505)),
            "longitude": float(deposito.get("longitude", -46.6333)),
            "demanda_kg": 0.0,
        }
    ]
    for p in pontos:
        nos.append(
            {
                "ponto_coleta_id": int(p["ponto_coleta_id"]),
                "ponto_nome": p.get("ponto_nome", f"Ponto #{p['ponto_coleta_id']}"),
                "latitude": float(p["latitude"]),
                "longitude": float(p["longitude"]),
                "demanda_kg": float(p.get("demanda_kg", p.get("peso_total_ponto_kg", 250.0))),
            }
        )

    matriz_dist = construir_matriz_distancias_haversine(nos)
    demandas_kg = [float(n["demanda_kg"]) for n in nos]
    capacidades_kg = [float(v.get("capacidade_carga_kg", 5000.0)) for v in veiculos_ordenados]

    # 1. Solução Ingênua (Ordem de entrada não otimizada) para comparação de economia
    rotas_ingenuas = construir_solucao_ingenua_sequencial(demandas_kg, capacidades_kg)
    dist_nao_otimizada = calcular_distancia_solucao(rotas_ingenuas, matriz_dist)

    # 2. Heurística Construtiva Gulosa (Nearest Neighbor) + VND inicial
    rotas_nn = construir_solucao_gulosa_nearest_neighbor(matriz_dist, demandas_kg, capacidades_kg)
    melhor_solucao = busca_local_vnd(rotas_nn, matriz_dist, demandas_kg, capacidades_kg)
    melhor_distancia = calcular_distancia_solucao(melhor_solucao, matriz_dist)

    # Garante que a solução inicial VNS seja pelo menos tão boa quanto a ordem original submetida ao VND
    if dist_nao_otimizada < melhor_distancia:
        melhor_solucao = busca_local_vnd(rotas_ingenuas, matriz_dist, demandas_kg, capacidades_kg)
        melhor_distancia = calcular_distancia_solucao(melhor_solucao, matriz_dist)

    # 3. Loop Principal do VNS (Shaking em N_k + Busca Local VND)
    k_max = 3
    for _ in range(max_iteracoes):
        k = 1
        while k <= k_max:
            solucao_perturbada = perturbar_solucao_shaking(
                melhor_solucao, k, demandas_kg, capacidades_kg, rng
            )
            solucao_refinada = busca_local_vnd(
                solucao_perturbada, matriz_dist, demandas_kg, capacidades_kg
            )
            dist_refinada = calcular_distancia_solucao(solucao_refinada, matriz_dist)

            if dist_refinada + 1e-6 < melhor_distancia:
                melhor_solucao = copy.deepcopy(solucao_refinada)
                melhor_distancia = dist_refinada
                k = 1
            else:
                k += 1

    # 4. Formatar resposta detalhada por rota/veículo
    rotas_formatadas: List[Dict[str, Any]] = []
    custo_total_brl = 0.0

    for idx, rota_nodes in enumerate(melhor_solucao):
        veic = veiculos_ordenados[idx % len(veiculos_ordenados)]
        dist_rota = calcular_distancia_rota(rota_nodes, matriz_dist)
        custo_km = float(veic.get("custo_por_km", 4.50))
        custo_rota = round(dist_rota * custo_km, 2)
        custo_total_brl += custo_rota

        carga_rota = round(sum(demandas_kg[n] for n in rota_nodes), 2)
        cap_veic = float(veic.get("capacidade_carga_kg", 5000.0))

        sequencia_visitas = [
            {
                "ordem": 0,
                "ponto_coleta_id": 0,
                "ponto_nome": nos[0]["ponto_nome"],
                "latitude": nos[0]["latitude"],
                "longitude": nos[0]["longitude"],
                "demanda_coletada_kg": 0.0,
            }
        ]
        for passo, node_idx in enumerate(rota_nodes, start=1):
            info_no = nos[node_idx]
            sequencia_visitas.append(
                {
                    "ordem": passo,
                    "ponto_coleta_id": info_no["ponto_coleta_id"],
                    "ponto_nome": info_no["ponto_nome"],
                    "latitude": info_no["latitude"],
                    "longitude": info_no["longitude"],
                    "demanda_coletada_kg": round(info_no["demanda_kg"], 2),
                }
            )
        sequencia_visitas.append(
            {
                "ordem": len(rota_nodes) + 1,
                "ponto_coleta_id": 0,
                "ponto_nome": nos[0]["ponto_nome"],
                "latitude": nos[0]["latitude"],
                "longitude": nos[0]["longitude"],
                "demanda_coletada_kg": 0.0,
            }
        )

        rotas_formatadas.append(
            {
                "veiculo_id": veic.get("id", idx + 1),
                "veiculo_placa": veic.get("placa", f"SRT{idx + 1}A00"),
                "veiculo_modelo": veic.get("modelo", "Caminhão Coletor"),
                "capacidade_veiculo_kg": cap_veic,
                "carga_total_rota_kg": carga_rota,
                "taxa_ocupacao_veiculo_pct": round((carga_rota / max(cap_veic, 1.0)) * 100.0, 2),
                "distancia_rota_km": round(dist_rota, 3),
                "custo_estimado_rota_brl": custo_rota,
                "quantidade_paradas": len(rota_nodes),
                "sequencia_ids": [nos[n]["ponto_coleta_id"] for n in rota_nodes],
                "sequencia_visitas": sequencia_visitas,
            }
        )

    economia_km = max(0.0, dist_nao_otimizada - melhor_distancia)
    economia_pct = (
        round((economia_km / dist_nao_otimizada) * 100.0, 2)
        if dist_nao_otimizada > 1e-6
        else 0.0
    )

    return {
        "algoritmo": "Variable Neighborhood Search (VNS + VND)",
        "max_iteracoes": max_iteracoes,
        "distancia_rota_nao_otimizada_km": round(dist_nao_otimizada, 3),
        "distancia_total_otimizada_km": round(melhor_distancia, 3),
        "economia_distancia_km": round(economia_km, 3),
        "percentual_economia_pct": economia_pct,
        "custo_total_estimado_brl": round(custo_total_brl, 2),
        "quantidade_rotas": len(rotas_formatadas),
        "rotas": rotas_formatadas,
    }
