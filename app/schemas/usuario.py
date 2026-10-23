from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="E-mail único do usuário")
    perfil: str = Field(default="OPERADOR", description="Perfil de acesso (ADMIN, GESTOR, OPERADOR, ANALISTA)")

    @field_validator("perfil")
    @classmethod
    def validate_perfil(cls, v: str) -> str:
        allowed = {"ADMIN", "GESTOR", "OPERADOR", "ANALISTA"}
        v_upper = v.strip().upper()
        if v_upper not in allowed:
            raise ValueError(f"Perfil inválido. Valores permitidos: {', '.join(sorted(allowed))}")
        return v_upper


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, max_length=100, description="Senha em texto plano (mínimo 6 caracteres)")


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str = Field(..., min_length=1)


class UsuarioResponse(UsuarioBase):
    id: int
    ativo: bool
    data_criacao: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: Optional[UsuarioResponse] = None
