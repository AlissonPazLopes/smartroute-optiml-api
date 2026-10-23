"""Modelos ORM do domínio."""
from app.models.historico_coleta import HistoricoColeta
from app.models.ponto_coleta import PontoColeta
from app.models.usuario import Usuario
from app.models.veiculo_frota import VeiculoFrota

__all__ = ["Usuario", "PontoColeta", "HistoricoColeta", "VeiculoFrota"]
