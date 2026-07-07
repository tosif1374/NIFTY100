from contextlib import asynccontextmanager
from pathlib import Path
import os
import sqlite3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .routers import company, financial, sectors, auth_routers
from .middleware import RateLimitMiddleware, log_requests


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown lifecycle.
    """
    db_path = os.getenv("DB_PATH", "./db/nifty100.db")
    snapshot_path = Path("./data/snapshots/company_summary.json")

    try:
        if not Path(db_path).exists():
            logger.warning(
                "nifty100.db not found at {}; API endpoints may fail",
                db_path,
            )
        else:
            conn = sqlite3.connect(db_path)
            count = conn.execute(
                "SELECT COUNT(*) FROM companies"
            ).fetchone()[0]
            conn.close()

            logger.info(
                "nifty100.db ready: {} companies loaded",
                count,
            )

        if not snapshot_path.exists():
            logger.warning(
                "company_summary.json missing; "
                "run src/analytics/export.py first"
            )
        else:
            logger.info(
                "Snapshots found at {}",
                snapshot_path.parent,
            )

    except Exception as e:
        logger.exception("Startup validation failed: {}", e)

    yield

    logger.info("API shutting down cleanly")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Nifty 100 Financial Analytics API",
        description=(
            "REST API for financial ratios, P&L analysis, "
            "balance sheet metrics, cash flow insights, "
            "price analytics, and sector comparisons."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware
    app.middleware("http")(log_requests)
    app.add_middleware(RateLimitMiddleware)

    # Routers
    app.include_router(
        auth_routers.router,
        tags=["Authentication"],
    )

    app.include_router(
        company.router,
        prefix="/api/v1",
        tags=["Company"],
    )

    app.include_router(
        financial.router,
        prefix="/api/v1",
        tags=["Financials"],
    )

    app.include_router(
        sectors.router,
        prefix="/api/v1",
        tags=["Sectors"],
    )

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "ok",
            "version": "1.0.0",
        }

    return app


app = create_app()