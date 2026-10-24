from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class HistoricoColeta(Base):
    __tablename__ = "historicos_coleta"

    id = Column(Integer, primary_key=True, index=True)
    ponto_coleta_id = Column(Integer, ForeignKey("pontos_coleta.id", ondelete="CASCADE"), nullable=False, index=True)
    data_coleta = Column(Date, nullable=False, index=True)
    dia_semana = Column(Integer, nullable=False, index=True)
    temperatura_media = Column(Float, nullable=False)
    evento_sazonal = Column(Boolean, nullable=False, default=False)
    peso_papelao_kg = Column(Float, nullable=False)
    peso_plastico_kg = Column(Float, nullable=False)
    peso_aluminio_kg = Column(Float, nullable=False)
    peso_total_kg = Column(Float, nullable=False)
    valor_estimado_brl = Column(Float, nullable=False)

    ponto_coleta = relationship("PontoColeta", back_populates="historicos")
