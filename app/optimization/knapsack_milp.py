"""
Motor de Programação Linear Inteira Mista (MILP) utilizando PuLP para resolução do
Problema da Mochila Multi-Material Capacitado (Peso e Volume).
"""
from typing import Any, Dict, List

import pulp

# Parâmetros físicos e econômicos por tipo de material reciclável
PARAMETROS_MATERIAIS: Dict[str, Dict[str, float]] = {
    "papelao": {
        "preco_por_kg_brl": 0.85,
        "volume_m3_por_kg": 0.0032,  # Densidade aparente ~312 kg/m³ (prensado/semicompactado)
        "co2_evitado_por_kg": 1.10,  # kg de CO2e evitado por kg reciclado
    },
    "plastico": {
        "preco_por_kg_brl": 2.40,
        "volume_m3_por_kg": 0.0045,  # Densidade aparente ~222 kg/m³
        "co2_evitado_por_kg": 1.85,
    },
    "aluminio": {
        "preco_por_kg_brl": 7.50,
        "volume_m3_por_kg": 0.0020,  # Densidade aparente ~500 kg/m³
        "co2_evitado_por_kg": 9.10,
    },
}


def resolver_alocacao_carga_pli(
    capacidade_peso_kg: float,
    capacidade_volume_m3: float,
    candidatos: List[Dict[str, Any]],
    peso_financeiro: float = 0.65,
    peso_ambiental: float = 0.35,
    permitir_coleta_parcial_por_material: bool = False,
) -> Dict[str, Any]:
    """
    Resolve o Problema da Mochila Multi-Material via Programação Linear Inteira (PuLP).

    Maximiza a função objetivo multi-critério composta pelo valor financeiro (R$),
    impacto ambiental (kg CO2e evitados) ponderados pela prioridade de esvaziamento de cada ponto,
    respeitando simultaneamente os limites de peso (kg) e volume (m³) do veículo coletor.
    """
    if not candidatos:
        return {
            "status_solver": "Optimal",
            "otimo_encontrado": True,
            "capacidade_peso_kg": capacidade_peso_kg,
            "capacidade_volume_m3": capacidade_volume_m3,
            "peso_total_alocado_kg": 0.0,
            "volume_total_alocado_m3": 0.0,
            "ocupacao_peso_pct": 0.0,
            "ocupacao_volume_pct": 0.0,
            "valor_financeiro_total_brl": 0.0,
            "impacto_ambiental_co2_kg": 0.0,
            "valor_funcao_objetivo": 0.0,
            "pontos_selecionados": [],
            "pontos_nao_atendidos_ids": [],
        }

    problema = pulp.LpProblem("SmartRoute_MultiMaterial_Knapsack_PLI", pulp.LpMaximize)

    materiais = ("papelao", "plastico", "aluminio")

    # Pré-cálculo de atributos por ponto e material
    dados_calc: Dict[int, Dict[str, Any]] = {}
    for item in candidatos:
        pid = int(item["ponto_coleta_id"])
        pesos = {
            "papelao": float(item.get("peso_papelao_kg", 0.0)),
            "plastico": float(item.get("peso_plastico_kg", 0.0)),
            "aluminio": float(item.get("peso_aluminio_kg", 0.0)),
        }
        prioridade = float(item.get("prioridade_coleta", 1.0))
        fator_prio = 1.0 + 0.08 * max(0.0, prioridade - 1.0)

        volumes = {
            m: round(pesos[m] * PARAMETROS_MATERIAIS[m]["volume_m3_por_kg"], 4)
            for m in materiais
        }
        valores_brl = {
            m: round(pesos[m] * PARAMETROS_MATERIAIS[m]["preco_por_kg_brl"], 2)
            for m in materiais
        }
        co2_kg = {
            m: round(pesos[m] * PARAMETROS_MATERIAIS[m]["co2_evitado_por_kg"], 2)
            for m in materiais
        }

        dados_calc[pid] = {
            "raw": item,
            "pesos": pesos,
            "volumes": volumes,
            "valores_brl": valores_brl,
            "co2_kg": co2_kg,
            "prioridade": prioridade,
            "fator_prio": fator_prio,
        }

    # Variáveis de decisão binárias y_{pid, m} in {0, 1}
    y_vars: Dict[tuple, pulp.LpVariable] = {}
    x_ponto_vars: Dict[int, pulp.LpVariable] = {}

    def _criar_var_binaria(nome: str) -> pulp.LpVariable:
        if hasattr(problema, "add_variable"):
            return problema.add_variable(nome, cat=pulp.LpBinary)
        return pulp.LpVariable(nome, cat=pulp.LpBinary)

    for pid in dados_calc:
        x_ponto_vars[pid] = _criar_var_binaria(f"visita_ponto_{pid}")
        for m in materiais:
            y_vars[(pid, m)] = _criar_var_binaria(f"coleta_{pid}_{m}")
            if not permitir_coleta_parcial_por_material:
                # Se não permitir coleta parcial por material, todos os materiais do ponto seguem x_ponto_vars[pid]
                problema += (y_vars[(pid, m)] - x_ponto_vars[pid] == 0), f"acoplamento_integral_{pid}_{m}"
            else:
                problema += (y_vars[(pid, m)] - x_ponto_vars[pid] <= 0), f"acoplamento_parcial_{pid}_{m}"

    # Função Objetivo: Maximizar utilidade combinada (Valor Financeiro + Impacto Ambiental) * Fator de Prioridade
    termos_objetivo = []
    for pid, info in dados_calc.items():
        fp = info["fator_prio"]
        for m in materiais:
            utilidade_item = fp * (
                peso_financeiro * info["valores_brl"][m] + peso_ambiental * info["co2_kg"][m]
            )
            termos_objetivo.append(utilidade_item * y_vars[(pid, m)])

    problema += pulp.lpSum(termos_objetivo), "Maximizar_Valor_Financeiro_Ambiental_Prioritario"

    # Restrição 1: Limite de Capacidade de Peso (kg)
    problema += (
        pulp.lpSum(
            dados_calc[pid]["pesos"][m] * y_vars[(pid, m)]
            for pid in dados_calc
            for m in materiais
        )
        <= capacidade_peso_kg,
        "Restricao_Capacidade_Peso_Kg",
    )

    # Restrição 2: Limite de Capacidade de Volume (m³)
    problema += (
        pulp.lpSum(
            dados_calc[pid]["volumes"][m] * y_vars[(pid, m)]
            for pid in dados_calc
            for m in materiais
        )
        <= capacidade_volume_m3,
        "Restricao_Capacidade_Volume_M3",
    )

    # Resolver usando CBC do PuLP sem logs verbosos no terminal
    solver = pulp.PULP_CBC_CMD(msg=False)
    status_code = problema.solve(solver)
    status_str = pulp.LpStatus.get(status_code, "Unknown")

    pontos_selecionados: List[Dict[str, Any]] = []
    pontos_nao_atendidos_ids: List[int] = []

    peso_total_alocado = 0.0
    volume_total_alocado = 0.0
    valor_total_brl = 0.0
    impacto_co2_total = 0.0

    for pid, info in dados_calc.items():
        materiais_coletados = [
            m for m in materiais if (pulp.value(y_vars[(pid, m)]) or 0.0) >= 0.5
        ]
        if materiais_coletados:
            peso_ponto = sum(info["pesos"][m] for m in materiais_coletados)
            vol_ponto = sum(info["volumes"][m] for m in materiais_coletados)
            val_ponto = sum(info["valores_brl"][m] for m in materiais_coletados)
            co2_ponto = sum(info["co2_kg"][m] for m in materiais_coletados)

            peso_total_alocado += peso_ponto
            volume_total_alocado += vol_ponto
            valor_total_brl += val_ponto
            impacto_co2_total += co2_ponto

            raw = info["raw"]
            pontos_selecionados.append(
                {
                    "ponto_coleta_id": pid,
                    "ponto_nome": raw.get("ponto_nome", f"Ponto #{pid}"),
                    "latitude": float(raw.get("latitude", -23.5505)),
                    "longitude": float(raw.get("longitude", -46.6333)),
                    "prioridade_coleta": info["prioridade"],
                    "materiais_coletados": materiais_coletados,
                    "peso_papelao_alocado_kg": round(
                        info["pesos"]["papelao"] if "papelao" in materiais_coletados else 0.0, 2
                    ),
                    "peso_plastico_alocado_kg": round(
                        info["pesos"]["plastico"] if "plastico" in materiais_coletados else 0.0, 2
                    ),
                    "peso_aluminio_alocado_kg": round(
                        info["pesos"]["aluminio"] if "aluminio" in materiais_coletados else 0.0, 2
                    ),
                    "peso_total_ponto_kg": round(peso_ponto, 2),
                    "volume_total_ponto_m3": round(vol_ponto, 4),
                    "valor_financeiro_ponto_brl": round(val_ponto, 2),
                    "impacto_ambiental_co2_kg": round(co2_ponto, 2),
                }
            )
        else:
            pontos_nao_atendidos_ids.append(pid)

    obj_val = float(pulp.value(problema.objective) or 0.0)
    ocup_peso = round((peso_total_alocado / max(capacidade_peso_kg, 1e-6)) * 100.0, 2)
    ocup_vol = round((volume_total_alocado / max(capacidade_volume_m3, 1e-6)) * 100.0, 2)

    return {
        "status_solver": status_str,
        "otimo_encontrado": status_str == "Optimal",
        "capacidade_peso_kg": round(capacidade_peso_kg, 2),
        "capacidade_volume_m3": round(capacidade_volume_m3, 4),
        "peso_total_alocado_kg": round(peso_total_alocado, 2),
        "volume_total_alocado_m3": round(volume_total_alocado, 4),
        "ocupacao_peso_pct": ocup_peso,
        "ocupacao_volume_pct": ocup_vol,
        "valor_financeiro_total_brl": round(valor_total_brl, 2),
        "impacto_ambiental_co2_kg": round(impacto_co2_total, 2),
        "valor_funcao_objetivo": round(obj_val, 4),
        "quantidade_pontos_selecionados": len(pontos_selecionados),
        "pontos_selecionados": pontos_selecionados,
        "pontos_nao_atendidos_ids": pontos_nao_atendidos_ids,
    }
