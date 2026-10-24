from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    auth_router,
    historicos_coleta_router,
    ml_router,
    optimization_router,
    pontos_coleta_router,
    seed_router,
    veiculos_frota_router,
)
from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import register_exception_handlers
import app.models  # noqa: F401

OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Monitoramento de disponibilidade e integridade do serviço.",
    },
    {
        "name": "Autenticação",
        "description": "Registro de usuários, autenticação OAuth2/JWT (JSON ou Form) e consulta de perfil autenticado.",
    },
    {
        "name": "Pontos de Coleta",
        "description": "Gerenciamento georreferenciado de ecopontos, capacidade de armazenamento, população atendida e perfil de zona urbana.",
    },
    {
        "name": "Histórico de Coletas",
        "description": "Registro e consulta paginada de coletas seletivas (papelão, plástico, alumínio, clima e sazonalidade).",
    },
    {
        "name": "Frota de Veículos",
        "description": "Controle operacional de caminhões coletores, capacidade de carga (kg), cubagem máxima (m³) e custo por km.",
    },
    {
        "name": "Data Seeder (Sintético ML)",
        "description": "Geração de cenários sintéticos realistas com correlações estatísticas reais para treinamento de modelos.",
    },
    {
        "name": "Machine Learning (Previsão de Demanda)",
        "description": "Engenharia de atributos, treinamento comparativo (Multiple Linear Regression vs Random Forest Regressor) com K-Fold Cross-Validation e inferência de demanda futura.",
    },
    {
        "name": "Otimização Combinatória (PLI PuLP & VNS CVRP)",
        "description": "Alocação ótima de carga via Programação Linear Inteira (Problema da Mochila Multi-Material com PuLP), Roteirização de Veículos Capacitada com Meta-heurística VNS (N1 Swap, N2 2-Opt, N3 Relocate) e Planejamento Integrado.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Plataforma Inteligente de Engenharia Logística e Ciência de Dados para Coleta Seletiva Urbana. "
            "Integra **Machine Learning (Scikit-Learn)** para previsão de demanda de recicláveis, "
            "**Programação Linear Inteira Mista (PuLP)** para seleção ótima de carga multi-material e "
            "**Meta-heurística Variable Neighborhood Search (VNS + VND)** para roteirização de frota (CVRP)."
        ),
        contact={
            "name": "Equipe de Engenharia SmartRoute OptiML",
            "url": "https://github.com/alissondev/smartroute-optiml-api",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=OPENAPI_TAGS,
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
    application.include_router(optimization_router.router, prefix=settings.API_PREFIX)

    @application.get(
        "/health",
        tags=["Health"],
        summary="Verificar status de saúde da API",
        description="Retorna o estado operacional da API, nome do projeto e versão ativa.",
    )
    def health_check():
        return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}

    return application


app = create_app()
