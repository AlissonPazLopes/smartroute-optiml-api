from sqlalchemy import Boolean, Column, Float, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class PontoColeta(Base):
    __tablename__ = "pontos_coleta"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), unique=True, nullable=False, index=True)
    bairro = Column(String(100), nullable=False, index=True)
    cidade = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    populacao_atendida = Column(Integer, nullable=False)
    tipo_zona = Column(String(50), nullable=False, index=True)
    capacidade_armazenamento_kg = Column(Float, nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)

    historicos = relationship(
        "HistoricoColeta",
        back_populates="ponto_coleta",
        cascade="all, delete-orphan",
    )
