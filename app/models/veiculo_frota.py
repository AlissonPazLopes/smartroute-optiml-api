from sqlalchemy import Boolean, Column, Float, Integer, String

from app.core.database import Base


class VeiculoFrota(Base):
    __tablename__ = "veiculos_frota"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(15), unique=True, nullable=False, index=True)
    modelo = Column(String(100), nullable=False)
    capacidade_carga_kg = Column(Float, nullable=False)
    volume_maximo_m3 = Column(Float, nullable=False)
    custo_por_km = Column(Float, nullable=False)
    disponivel = Column(Boolean, nullable=False, default=True, index=True)
