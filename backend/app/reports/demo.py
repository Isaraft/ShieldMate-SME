"""Public synthetic data: no authentication, database session, scan or tenant dependency."""

from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response
from pydantic import BaseModel, ConfigDict

from app.domain_limits import DomainLimiter
from app.errors import PublicError
from app.reports.pdf import render
from app.reports.schemas import Locale, Snapshot

router = APIRouter(prefix="/demo")
limiter = DomainLimiter()
pdf_lock = Lock()


class DemoQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    locale: Locale = "en"


def sample(locale: Locale = "en") -> Snapshot:
    snapshot = Snapshot.model_validate_json(
        (Path(__file__).parent / "demo_snapshot.json").read_text(encoding="utf-8")
    )
    if snapshot.kind != "demo":
        raise PublicError(503, "Sample data unavailable")
    return snapshot.model_copy(update={"locale": locale})


@router.get("", response_model=Snapshot)
def data(filters: Annotated[DemoQuery, Query()]) -> Snapshot:
    return sample(filters.locale)


@lru_cache(maxsize=2)
def cached_pdf(locale: Locale) -> bytes:
    return render(sample(locale))


def sample_pdf(locale: Locale) -> bytes:
    if not pdf_lock.acquire(blocking=False):
        raise PublicError(429, "Sample report is being prepared. Retry shortly.")
    try:
        return cached_pdf(locale)
    finally:
        pdf_lock.release()


@router.get("/report")
def download(filters: Annotated[DemoQuery, Query()], request: Request) -> Response:
    try:
        limiter.check(request.client.host if request.client else "unknown", 12)
    except PublicError:
        raise PublicError(429, "Too many sample downloads. Retry later.") from None
    return Response(
        sample_pdf(filters.locale),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="shieldmate-DEMO-{filters.locale}.pdf"',
            "Cache-Control": "private, no-store",
        },
    )
