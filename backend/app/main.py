from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_v1_router
import app.models  # Register all domain models on Base.metadata

app = FastAPI(
    title="Gieni Acquisition Decision Intelligence Platform",
    version="2.0.0",
    description="Deterministic Acquisition Engine, 14-Stage OLE, and Quality Control Gatekeeper."
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
