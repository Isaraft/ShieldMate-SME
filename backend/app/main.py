import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.health import router as health_router
from app.api.readiness import router as readiness_router
from app.auth import router as auth_router
from app.config import BACKEND_ROOT, Settings
from app.dashboard import router as dashboard_router
from app.db import Database
from app.domain_dns import check_txt
from app.domain_limits import DomainLimiter
from app.domains import router as domains_router
from app.errors import (
    http_error,
    unexpected_error,
    validation_error,
)
from app.findings.api import router as findings_router
from app.http_security import SecurityBoundary
from app.reports.api import router as reports_router
from app.reports.demo import router as demo_router
from app.scanner.service import router as scans_router
from app.tasks.api import router as tasks_router

logger = logging.getLogger("shieldmate")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.expected_revision = ScriptDirectory.from_config(
            Config(str(BACKEND_ROOT / "alembic.ini"))
        ).get_current_head()
        app.state.database = Database(settings.database_url)
        logger.info("service_started phase=00")
        try:
            yield
        finally:
            app.state.database.close()
            logger.info("service_stopped")

    app = FastAPI(
        title="ShieldMate API",
        debug=False,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_exception_handler(HTTPException, http_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unexpected_error)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=False,
            allow_methods=["GET"],
            allow_headers=[],
        )

    app.add_middleware(SecurityBoundary)

    app.state.settings = settings
    app.state.check_txt = check_txt
    app.state.domain_limiter = DomainLimiter()
    app.state.bootstrap_limiter = DomainLimiter()
    app.state.task_limiter = DomainLimiter()
    app.state.report_limiter = DomainLimiter()
    app.include_router(domains_router, prefix="/api/v1")
    app.include_router(scans_router, prefix="/api/v1")
    app.include_router(findings_router, prefix="/api/v1")
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")
    app.include_router(demo_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(readiness_router, prefix="/api/v1")
    return app


app = create_app()
