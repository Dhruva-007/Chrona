import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.errors import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.api.routes import graph, incidents, simulation, narrative, agent, telemetry
from app.services.memgraph import get_driver, close_driver, ping

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle manager."""
    logger.info("Chrona API starting up...")
    try:
        get_driver()
        if ping():
            logger.info("✅ Memgraph connection established")
        else:
            logger.warning("⚠️  Memgraph not reachable - graph features will fail")
    except Exception as exc:
        logger.warning(f"⚠️  Could not connect to Memgraph at startup: {exc}")
    yield
    logger.info("Chrona API shutting down...")
    close_driver()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Time-travel debugging for your entire infrastructure.",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ALLOW_ALL_CORS else [settings.FRONTEND_URL],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(graph.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")
app.include_router(narrative.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")
app.include_router(telemetry.router, prefix="/api/v1")

# ---------------------------------------------------------------------------
# Root routes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["System"])
async def health_check() -> dict:
    memgraph_ok = ping()
    return {
        "status": "healthy" if memgraph_ok else "degraded",
        "service": "chrona-core",
        "version": settings.VERSION,
        "memgraph": "connected" if memgraph_ok else "unreachable",
    }


@app.get("/", tags=["System"])
async def root() -> dict:
    return {
        "message": "Chrona API is running",
        "version": settings.VERSION,
        "docs": "/docs",
    }