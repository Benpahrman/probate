import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any, cast

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from honeybadger import honeybadger, contrib
from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.router import api_v1_router
import app.models  # Register all domain models on Base.metadata

if settings.HONEYBADGER_API_KEY:
    honeybadger.configure(
        api_key=settings.HONEYBADGER_API_KEY,
        environment=settings.ENVIRONMENT,
        insights_enabled=settings.HONEYBADGER_INSIGHTS_ENABLED,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Gieni Acquisition Decision Intelligence Platform",
    version="2.0.0",
    description="Deterministic Acquisition Engine, 14-Stage OLE, and Quality Control Gatekeeper.",
    lifespan=lifespan,
)

if settings.HONEYBADGER_API_KEY:
    app.add_middleware(
        cast(Any, contrib.ASGIHoneybadger),
        params_filters=["password", "secret", "token", "sensitive_data", "api_key", "authorization"]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/health", tags=["Infrastructure"])
def health_check():
    return {"status": "HEALTHY", "version": settings.VERSION, "environment": settings.ENVIRONMENT}


# Mount Unified SPA Frontend
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/favicon.svg", include_in_schema=False)
    def favicon():
        favicon_file = FRONTEND_DIST / "favicon.svg"
        if favicon_file.exists():
            return FileResponse(str(favicon_file))
        return None

    @app.get("/portal", include_in_schema=False)
    @app.get("/app", include_in_schema=False)
    @app.get("/", include_in_schema=False)
    def serve_frontend():
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"status": "SPA_NOT_FOUND"}
