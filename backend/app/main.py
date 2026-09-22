from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from honeybadger import honeybadger, contrib
from app.core.config import settings
from app.api.v1.router import api_v1_router
import app.models  # Register all domain models on Base.metadata

if settings.HONEYBADGER_API_KEY:
    honeybadger.configure(
        api_key=settings.HONEYBADGER_API_KEY,
        environment=settings.ENVIRONMENT,
        insights_enabled=settings.HONEYBADGER_INSIGHTS_ENABLED,
    )

app = FastAPI(
    title="Gieni Acquisition Decision Intelligence Platform",
    version="2.0.0",
    description="Deterministic Acquisition Engine, 14-Stage OLE, and Quality Control Gatekeeper."
)

if settings.HONEYBADGER_API_KEY:
    app.add_middleware(
        contrib.ASGIHoneybadger,
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
