from pydantic import BaseModel, Field


class SeedRequest(BaseModel):
    dias_historico: int = Field(default=45, ge=40, le=365, description="Quantidade de dias de histórico por ponto (mínimo 40 para superar 1.000 registros com 25 pontos)")
    limpar_antes: bool = Field(default=True, description="Se verdadeiro, limpa registros anteriores de pontos, veículos e históricos antes de popular")
    random_seed: int = Field(default=42, description="Semente aleatória para reprodutibilidade")


class SeedResponse(BaseModel):
    sucesso: bool
    mensagem: str
    pontos_coleta_criados: int
    veiculos_criados: int
    historicos_criados: int
    correlacao_populacao_peso: float
