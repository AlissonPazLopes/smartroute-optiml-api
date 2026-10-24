from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, ForbiddenException, UnauthorizedException
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import TokenResponse, UsuarioCreate, UsuarioResponse


class AuthService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)

    def registrar_usuario(self, dados: UsuarioCreate) -> Usuario:
        existente = self.repo.get_by_email(dados.email)
        if existente:
            raise ConflictException(f"Já existe um usuário cadastrado com o e-mail '{dados.email}'.")

        senha_hash = get_password_hash(dados.senha)
        return self.repo.create(
            nome=dados.nome,
            email=dados.email,
            senha_hash=senha_hash,
            perfil=dados.perfil,
        )

    def autenticar(self, email: str, senha: str) -> TokenResponse:
        usuario = self.repo.get_by_email(email)
        if not usuario or not verify_password(senha, usuario.senha_hash):
            raise UnauthorizedException("Credenciais inválidas: e-mail ou senha incorretos.")

        if not usuario.ativo:
            raise ForbiddenException("Conta de usuário desativada.")

        token = create_access_token(
            subject=usuario.email,
            extra_claims={"user_id": usuario.id, "perfil": usuario.perfil},
        )
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            usuario=UsuarioResponse.model_validate(usuario),
        )
