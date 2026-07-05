from contextlib import asynccontextmanager
from pathlib import Path
import os
import sqlite3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .routers import company, financials, sectors, auth_router
from .middleware import RateLimitMiddleware, log_requests


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown lifecycle.
    On startup: verify nifty100.db is accessible and snapshots exist.
    On shutdown: log clean exit.
    """
    db_path = os.getenv("DB_PATH", "./db/nifty100.db")
    snapshot_path = Path("./data/snapshots/company_summary.json")

    if not Path(db_path).exists():
        logger.warning("nifty100.db not found at {}; live endpoints will fail", db_path)
    else:
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        conn.close()
        logger.info("nifty100.db ready: {} companies", count)

    if not snapshot_path.exists():
        logger.warning("company_summary.json missing; run src/analytics/export.py first")
    else:
        logger.info("Snapshots found at {}", snapshot_path.parent)

    yield

    logger.info("API shutting down cleanly")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Nifty 100 Financial Analytics API",
        description=(
            "REST API serving financial ratios, P&L trends, balance sheet health, "
            "cash flow quality, price analytics, and sector comparisons for all "
            "100 Nifty 100 constituents. Built on top of the Sprint 2 analytics layer."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allow any origin in development; tighten in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.middleware("http")(log_requests)
    app.add_middleware(RateLimitMiddleware)

    # Register routers
    app.include_router(auth_router.router, tags=["Authentication"])
    app.include_router(company.router, prefix="/api/v1", tags=["Company"])
    app.include_router(financials.router, prefix="/api/v1", tags=["Financials"])
    app.include_router(sectors.router, prefix="/api/v1", tags=["Sectors"])

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok", "version": "1.0.0"}

    return app


app = create_app()