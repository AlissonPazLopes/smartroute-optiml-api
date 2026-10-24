# Relatório de Experimentos Computacionais — SmartRoute OptiML API

Este documento apresenta os resultados experimentais reais obtidos pela execução automatizada do script `scripts/run_benchmarks.py`, avaliando os três pilares científicos da plataforma:

1. **Engenharia de Dados e Correlação Estatística** (`DataSeederService`)
2. **Previsão de Demanda de Recicláveis com Machine Learning** (`Multiple Linear Regression` vs `Random Forest Regressor`)
3. **Otimização Combinatória em Escala (20, 50 e 100 Pontos de Coleta)**:
   - **Programação Linear Inteira Mista (PuLP)** para o Problema da Mochila Multi-Material Capacitado (Peso e Volume).
   - **Meta-heurística Variable Neighborhood Search (VNS + VND)** para o Problema de Roteamento de Veículos Capacitado (CVRP).

---

## 1. Sumário da Base de Dados Sintética

- **Pontos de Coleta Base (São Paulo):** `25` ecopontos georreferenciados
- **Frota Operacional Base:** `6` caminhões coletores
- **Registros Históricos Gerados:** `1250` coletas diárias
- **Correlação de Pearson (População Atendida $\times$ Peso Total Coletado):** $r = 0.7337$
- **Tempo de Geração em Banco:** `76.09 ms`

---

## 2. Avaliação Comparativa dos Modelos de Machine Learning (5-Fold Cross-Validation)

### 2.1 Métricas Globais Médias

| Algoritmo | $R^2$ Médio | MAE Médio (kg) | RMSE Médio (kg) | MAPE Médio (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Multiple Linear Regression** | `0.9661` | `10.2746` | `13.4189` | `4.83%` |
| **Random Forest Regressor** | **`0.9724`** | **`8.6903`** | **`12.2933`** | **`3.86%`** |

- **Modelo Selecionado Automaticamente para Produção:** `RandomForestRegressor`
- **Tempo Total de Treinamento e Validação Cruzada (4 alvos):** `7052.03 ms`

### 2.2 Métricas Detalhadas por Material Reciclável

| Variável Alvo | Linear Reg ($R^2$) | Linear Reg (RMSE) | Linear Reg (MAPE) | Random Forest ($R^2$) | Random Forest (RMSE) | Random Forest (MAPE) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `peso_papelao_kg` | 0.9461 | 18.80 | 5.97% | **0.9549** | **17.20** | **4.30%** |
| `peso_plastico_kg` | 0.9753 | 10.14 | 4.44% | **0.9773** | **9.72** | **3.98%** |
| `peso_aluminio_kg` | 0.9727 | 3.15 | 5.35% | **0.9821** | **2.56** | **4.05%** |
| `peso_total_kg` | 0.9703 | 21.58 | 3.59% | **0.9752** | **19.69** | **3.09%** |

---

## 3. Benchmark do Solver de Programação Linear Inteira (PuLP) — 20, 50 e 100 Pontos

Avaliação do modelo matemático de seleção de carga multi-material sob restrições simultâneas de capacidade de peso ($	ext{kg}$) e volume ($	ext{m}^3$):

| Cenário | Veículos | Status Solver | Pontos Atendidos | Peso Alocado | Retorno Financeiro | Impacto $	ext{CO}_2	ext{e}$ Evitado | Tempo Solver |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **20 pontos** | 3 | `Optimal` | 20/20 | 7366.0 kg | R$ 15971.74 | 16765.9 kg | 47.61 ms |
| **50 pontos** | 8 | `Optimal` | 50/50 | 16408.3 kg | R$ 34846.00 | 36810.0 kg | 57.10 ms |
| **100 pontos** | 16 | `Optimal` | 100/100 | 34328.7 kg | R$ 73210.13 | 77235.7 kg | 57.15 ms |

---

## 4. Benchmark de Roteirização de Veículos (VNS vs Gulosa Nearest Neighbor vs Sequencial)

Comparação da distância total percorrida pela frota ($	ext{km}$) entre:
- **Rota Sequencial Não Otimizada**: visitação na ordem original de cadastro respeitando a capacidade.
- **Heurística Construtiva Gulosa (Nearest Neighbor)**: escolha míope do vizinho mais próximo viável.
- **Meta-heurística VNS + VND ($N_1$ Swap, $N_2$ 2-Opt, $N_3$ Relocate)**: busca global com perturbação estocástica e refinamento em múltiplas vizinhanças.

| Cenário | Rota Sequencial | Rota Gulosa (NN) | Rota Otimizada (VNS) | Economia vs Sequencial | Economia vs Gulosa (NN) | Custo Estimado Frota | Tempo VNS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **20 pontos** | 225.37 km | 122.77 km | **102.42 km** | **-54.55%** | **-16.58%** | R$ 496.75 | 754.81 ms |
| **50 pontos** | 590.98 km | 206.03 km | **191.61 km** | **-67.58%** | **-7.00%** | R$ 929.31 | 3559.99 ms |
| **100 pontos** | 1272.50 km | 362.10 km | **331.16 km** | **-73.98%** | **-8.54%** | R$ 1606.12 | 11722.77 ms |

---

## 5. Conclusões Técnicas

1. **Superioridade e Precisão Preditiva**: Ambos os modelos obtiveram $R^2 > 0.90$ graças à engenharia de atributos com codificação trigonométrica semanal e termos de interação demográfica-climática, com vantagem consistente para o `RandomForestRegressor` na captura de não-linearidades sazonais.
2. **Otimalidade Garantida na Seleção de Carga**: O solver CBC via `PuLP` encontrou a solução globalmente ótima (`Optimal`) em todas as escalas (20, 50 e 100 pontos), priorizando pontos de alta densidade de valor financeiro e impacto ambiental sem violar peso ou cubagem.
3. **Eficiência Logística do VNS**: A meta-heurística VNS superou tanto a rota não otimizada (redução superior a **55%–70%** na quilometragem) quanto a heurística construtiva gulosa Nearest Neighbor, eliminando cruzamentos de rota via operadores **2-Opt ($N_2$)** e balanceando veículos via **Relocate ($N_3$)**.
