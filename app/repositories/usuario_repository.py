from typing import Optional

from sqlalchemy.orm import Session

from app.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, usuario_id: int) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.id == usuario_id).first()

    def get_by_email(self, email: str) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def create(self, nome: str, email: str, senha_hash: str, perfil: str = "OPERADOR", ativo: bool = True) -> Usuario:
        usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            perfil=perfil,
            ativo=ativo,
        )
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
