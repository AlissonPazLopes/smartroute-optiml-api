from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import AppException
from app.models.usuario import Usuario
from app.schemas.usuario import TokenResponse, UsuarioCreate, UsuarioResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/registro",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
)
@router.post(
    "/register",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def registrar(dados: UsuarioCreate, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.registrar_usuario(dados)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Autenticar usuário (JSON ou OAuth2 Form)",
)
async def login(
    request: Request,
    db: Session = Depends(get_db),
):
    content_type = request.headers.get("content-type", "")
    email: Optional[str] = None
    senha: Optional[str] = None

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        email = form.get("username") or form.get("email")
        senha = form.get("password") or form.get("senha")
    else:
        try:
            body = await request.json()
            if isinstance(body, dict):
                email = body.get("email") or body.get("username")
                senha = body.get("senha") or body.get("password")
        except Exception:
            pass

    if not email or not senha:
        raise AppException(
            "Credenciais ausentes. Informe email/senha (JSON) ou username/password (Form).",
            status_code=422,
        )

    service = AuthService(db)
    return service.autenticar(str(email), str(senha))


@router.get(
    "/me",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter dados do usuário autenticado",
)
def obter_usuario_atual(current_user: Usuario = Depends(get_current_user)):
    return current_user
