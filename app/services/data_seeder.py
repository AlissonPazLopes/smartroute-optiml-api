from datetime import date, timedelta
from typing import List

import numpy as np
from sqlalchemy.orm import Session

from app.models.historico_coleta import HistoricoColeta
from app.models.ponto_coleta import PontoColeta
from app.models.veiculo_frota import VeiculoFrota
from app.schemas.seeder import SeedRequest, SeedResponse


PONTOS_BASE_SP = [
    ("Ecoponto Pinheiros", "Pinheiros", "São Paulo", -23.5614, -46.7016, 42000, "COMERCIAL", 2500.0),
    ("Ecoponto Vila Mariana", "Vila Mariana", "São Paulo", -23.5891, -46.6347, 54000, "RESIDENCIAL", 2800.0),
    ("Ecoponto Mooca", "Mooca", "São Paulo", -23.5558, -46.5967, 48000, "MISTA", 2600.0),
    ("Ecoponto Itaim Bibi", "Itaim Bibi", "São Paulo", -23.5844, -46.6784, 39000, "COMERCIAL", 2400.0),
    ("Ecoponto Tatuapé", "Tatuapé", "São Paulo", -23.5401, -46.5766, 58000, "RESIDENCIAL", 3000.0),
    ("Ecoponto Santana", "Santana", "São Paulo", -23.5019, -46.6247, 51000, "RESIDENCIAL", 2700.0),
    ("Ecoponto Lapa", "Lapa", "São Paulo", -23.5235, -46.7023, 36000, "MISTA", 2200.0),
    ("Ecoponto Santo Amaro", "Santo Amaro", "São Paulo", -23.6542, -46.7095, 62000, "INDUSTRIAL", 3500.0),
    ("Ecoponto Ipiranga", "Ipiranga", "São Paulo", -23.5855, -46.6098, 44000, "MISTA", 2500.0),
    ("Ecoponto Perdizes", "Perdizes", "São Paulo", -23.5367, -46.6742, 47000, "RESIDENCIAL", 2600.0),
    ("Ecoponto Bela Vista", "Bela Vista", "São Paulo", -23.5612, -46.6478, 53000, "COMERCIAL", 2900.0),
    ("Ecoponto Brás", "Brás", "São Paulo", -23.5453, -46.6164, 49000, "COMERCIAL", 3200.0),
    ("Ecoponto Barra Funda", "Barra Funda", "São Paulo", -23.5261, -46.6634, 31000, "INDUSTRIAL", 2800.0),
    ("Ecoponto Jabaquara", "Jabaquara", "São Paulo", -23.6462, -46.6411, 59000, "RESIDENCIAL", 3100.0),
    ("Ecoponto Penha", "Penha", "São Paulo", -23.5239, -46.5412, 46000, "RESIDENCIAL", 2400.0),
    ("Ecoponto Butantã", "Butantã", "São Paulo", -23.5718, -46.7082, 41000, "MISTA", 2300.0),
    ("Ecoponto Campo Belo", "Campo Belo", "São Paulo", -23.6231, -46.6694, 34000, "RESIDENCIAL", 2100.0),
    ("Ecoponto Vila Prudente", "Vila Prudente", "São Paulo", -23.5829, -46.5811, 45000, "MISTA", 2500.0),
    ("Ecoponto Casa Verde", "Casa Verde", "São Paulo", -23.5082, -46.6561, 38000, "RESIDENCIAL", 2200.0),
    ("Ecoponto Bom Retiro", "Bom Retiro", "São Paulo", -23.5284, -46.6382, 33000, "COMERCIAL", 2700.0),
    ("Ecoponto Jurubatuba", "Jurubatuba", "São Paulo", -23.6712, -46.6981, 55000, "INDUSTRIAL", 3600.0),
    ("Ecoponto Saúde", "Saúde", "São Paulo", -23.6152, -46.6375, 43000, "RESIDENCIAL", 2400.0),
    ("Ecoponto Liberdade", "Liberdade", "São Paulo", -23.5594, -46.6319, 37000, "COMERCIAL", 2300.0),
    ("Ecoponto Vila Leopoldina", "Vila Leopoldina", "São Paulo", -23.5289, -46.7278, 35000, "INDUSTRIAL", 3000.0),
    ("Ecoponto Consolação", "Consolação", "São Paulo", -23.5531, -46.6584, 40000, "COMERCIAL", 2500.0),
]

VEICULOS_FROTA_BASE = [
    ("SRT1A01", "Volkswagen Delivery 9.170 Compactador", 4200.0, 14.0, 4.20, True),
    ("SRT2B02", "Mercedes-Benz Accelo 1016 Eco", 4800.0, 16.0, 4.65, True),
    ("SRT3C03", "Iveco Tector 15-210 Coletor Seletivo", 7500.0, 22.0, 5.80, True),
    ("SRT4D04", "Ford Cargo 1119 Baú Reciclagem", 5200.0, 18.0, 4.90, True),
    ("SRT5E05", "Volkswagen Constellation 17.280 Compactador", 9500.0, 28.0, 6.95, True),
    ("SRT6F06", "Mercedes-Benz Atego 1419 VUC Urbano", 3800.0, 12.0, 3.90, True),
]


class DataSeederService:
    def __init__(self, db: Session):
        self.db = db

    def gerar_dados(self, config: SeedRequest = SeedRequest()) -> SeedResponse:
        rng = np.random.default_rng(config.random_seed)

        if config.limpar_antes:
            self.db.query(HistoricoColeta).delete()
            self.db.query(PontoColeta).delete()
            self.db.query(VeiculoFrota).delete()
            self.db.commit()

        # 1. Criar 25 Pontos de Coleta
        pontos_criados: List[PontoColeta] = []
        for (
            nome,
            bairro,
            cidade,
            lat,
            lon,
            populacao,
            zona,
            cap_kg,
        ) in PONTOS_BASE_SP:
            existente = self.db.query(PontoColeta).filter(PontoColeta.nome == nome).first()
            if existente:
                pontos_criados.append(existente)
                continue

            ponto = PontoColeta(
                nome=nome,
                bairro=bairro,
                cidade=cidade,
                latitude=lat,
                longitude=lon,
                populacao_atendida=populacao,
                tipo_zona=zona,
                capacidade_armazenamento_kg=cap_kg,
                ativo=True,
            )
            self.db.add(ponto)
            pontos_criados.append(ponto)

        # 2. Criar 6 Veículos da Frota
        veiculos_criados: List[VeiculoFrota] = []
        for placa, modelo, cap_kg, vol_m3, custo_km, disp in VEICULOS_FROTA_BASE:
            existente_v = self.db.query(VeiculoFrota).filter(VeiculoFrota.placa == placa).first()
            if existente_v:
                veiculos_criados.append(existente_v)
                continue

            veiculo = VeiculoFrota(
                placa=placa,
                modelo=modelo,
                capacidade_carga_kg=cap_kg,
                volume_maximo_m3=vol_m3,
                custo_por_km=custo_km,
                disponivel=disp,
            )
            self.db.add(veiculo)
            veiculos_criados.append(veiculo)

        self.db.flush()

        # 3. Criar > 1.000 registros históricos com correlações reais
        dias_historico = max(config.dias_historico, 42)  # 25 * 42 = 1.050 registros no mínimo
        data_base = date.today() - timedelta(days=dias_historico)

        multiplicadores_zona = {
            "COMERCIAL": {"papelao": 1.45, "plastico": 0.95, "aluminio": 0.85},
            "RESIDENCIAL": {"papelao": 0.90, "plastico": 1.35, "aluminio": 1.25},
            "INDUSTRIAL": {"papelao": 1.55, "plastico": 1.40, "aluminio": 1.15},
            "MISTA": {"papelao": 1.15, "plastico": 1.15, "aluminio": 1.05},
        }

        historicos_batch: List[HistoricoColeta] = []
        populacoes_amostra: List[float] = []
        pesos_totais_amostra: List[float] = []

        for dia_idx in range(dias_historico):
            data_atual = data_base + timedelta(days=dia_idx)
            dia_semana = data_atual.weekday()  # 0=Seg .. 6=Dom

            # Temperatura sazonal realista + variação diária
            temp_base = 23.5 + 4.5 * np.sin(2 * np.pi * dia_idx / 30.0)
            temperatura_dia = float(np.clip(temp_base + rng.normal(0, 1.8), 14.0, 36.0))

            # Evento sazonal em ~15% dos dias (ex: vésperas, feriados ou eventos municipais)
            evento_sazonal = bool(dia_idx % 9 == 0 or (dia_semana == 5 and dia_idx % 2 == 0))
            fator_sazonal = 1.35 if evento_sazonal else 1.00

            # Fator dia da semana: fim de semana aumenta plástico/alumínio, dias úteis aumentam papelão
            eh_fim_de_semana = dia_semana in (5, 6)
            fator_dia_papelao = 0.82 if eh_fim_de_semana else (1.18 if dia_semana in (0, 2, 4) else 1.05)
            fator_dia_plastico = 1.28 if eh_fim_de_semana else 0.96
            fator_dia_aluminio = 1.42 if eh_fim_de_semana else 0.90

            # Temperatura mais alta eleva consumo de bebidas (plástico PET e latas de alumínio)
            fator_temp_bebidas = 1.0 + max(0.0, (temperatura_dia - 20.0) * 0.022)

            for ponto in pontos_criados:
                fator_pop = ponto.populacao_atendida / 1000.0
                mult_z = multiplicadores_zona.get(ponto.tipo_zona, multiplicadores_zona["MISTA"])

                base_papelao = fator_pop * 4.2 * mult_z["papelao"] * fator_dia_papelao * fator_sazonal
                base_plastico = (
                    fator_pop * 2.6 * mult_z["plastico"] * fator_dia_plastico * fator_temp_bebidas * fator_sazonal
                )
                base_aluminio = (
                    fator_pop * 0.75 * mult_z["aluminio"] * fator_dia_aluminio * fator_temp_bebidas * fator_sazonal
                )

                peso_papelao = round(float(max(5.0, base_papelao * rng.normal(1.0, 0.04))), 2)
                peso_plastico = round(float(max(3.0, base_plastico * rng.normal(1.0, 0.04))), 2)
                peso_aluminio = round(float(max(1.0, base_aluminio * rng.normal(1.0, 0.04))), 2)

                peso_total = round(peso_papelao + peso_plastico + peso_aluminio, 2)
                valor_estimado = round(
                    peso_papelao * 0.85 + peso_plastico * 2.40 + peso_aluminio * 7.50,
                    2,
                )

                historicos_batch.append(
                    HistoricoColeta(
                        ponto_coleta_id=ponto.id,
                        data_coleta=data_atual,
                        dia_semana=dia_semana,
                        temperatura_media=round(temperatura_dia, 1),
                        evento_sazonal=evento_sazonal,
                        peso_papelao_kg=peso_papelao,
                        peso_plastico_kg=peso_plastico,
                        peso_aluminio_kg=peso_aluminio,
                        peso_total_kg=peso_total,
                        valor_estimado_brl=valor_estimado,
                    )
                )
                populacoes_amostra.append(float(ponto.populacao_atendida))
                pesos_totais_amostra.append(peso_total)

        self.db.bulk_save_objects(historicos_batch)
        self.db.commit()

        corr_matrix = np.corrcoef(populacoes_amostra, pesos_totais_amostra)
        correlacao_pop_peso = round(float(corr_matrix[0, 1]), 4)

        return SeedResponse(
            sucesso=True,
            mensagem="Base de dados sintética populada com sucesso para treinamento de Machine Learning e otimização de rotas.",
            pontos_coleta_criados=len(pontos_criados),
            veiculos_criados=len(veiculos_criados),
            historicos_criados=len(historicos_batch),
            correlacao_populacao_peso=correlacao_pop_peso,
        )
