"""Readiness is distinct from liveness: the configured DB and migration head must be usable."""

from fastapi import APIRouter, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.auth import DB
from app.errors import PublicError

router = APIRouter()


@router.get("/health/ready")
def readiness(request: Request, db: DB) -> dict[str, str]:
    try:
        revision = db.scalar(text("SELECT version_num FROM alembic_version"))
        if revision != request.app.state.expected_revision:
            raise PublicError(503, "Service storage is not ready. Retry later.")
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise PublicError(503, "Service storage is not ready. Retry later.") from None
    return {"status": "ready"}
