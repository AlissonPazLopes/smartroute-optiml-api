from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    auth_router,
    historicos_coleta_router,
    ml_router,
    pontos_coleta_router,
    seed_router,
    veiculos_frota_router,
)
from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import register_exception_handlers
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="API REST para Otimização Logística de Coleta Seletiva e Previsão de Demanda com Machine Learning.",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)

    application.include_router(auth_router.router, prefix=settings.API_PREFIX)
    application.include_router(pontos_coleta_router.router, prefix=settings.API_PREFIX)
    application.include_router(historicos_coleta_router.router, prefix=settings.API_PREFIX)
    application.include_router(veiculos_frota_router.router, prefix=settings.API_PREFIX)
    application.include_router(seed_router.router, prefix=settings.API_PREFIX)
    application.include_router(ml_router.router, prefix=settings.API_PREFIX)

    @application.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}

    return application


app = create_app()
