from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedException("Token inválido ou expirado.")

    email = payload.get("sub")
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        raise UnauthorizedException("Usuário não encontrado.")
    if not user.ativo:
        raise ForbiddenException("Usuário inativo.")
    return user
