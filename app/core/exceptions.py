from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Recurso não encontrado", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, details=details)


class ConflictException(AppException):
    def __init__(self, message: str = "Conflito de dados", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT, details=details)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Não autorizado", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Acesso negado", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)


def build_error_payload(status_code: int, error: str, message: str, path: str, details: Any = None) -> dict:
    payload = {
        "sucesso": False,
        "status_code": status_code,
        "erro": error,
        "mensagem": message,
        "detail": message,
        "caminho": path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if details is not None:
        payload["detalhes"] = details
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_payload(
                status_code=exc.status_code,
                error=exc.__class__.__name__,
                message=exc.message,
                path=str(request.url.path),
                details=exc.details,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_payload(
                status_code=exc.status_code,
                error="HTTPException",
                message=str(exc.detail),
                path=str(request.url.path),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        sanitized_errors = []
        for err in exc.errors():
            sanitized_errors.append(
                {
                    "loc": list(err.get("loc", [])),
                    "msg": err.get("msg", ""),
                    "type": err.get("type", ""),
                }
            )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=build_error_payload(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error="ValidationError",
                message="Erro de validação nos dados enviados.",
                path=str(request.url.path),
                details=sanitized_errors,
            ),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=build_error_payload(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="InternalServerError",
                message="Erro interno inesperado no servidor.",
                path=str(request.url.path),
                details=str(exc),
            ),
        )
