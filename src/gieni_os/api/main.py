"""
Gieni OS - Core Platform API Service (Canonical Package)
"""

import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from gieni_os.database.connection import init_db, get_db
from gieni_os.api.routes import (
    counties,
    clients,
    cases,
    opportunities,
    workflow,
    exceptions,
    dashboard,
    ai_investigator,
    client_portal,
    ingestion,
    research,
    llm,
    intelligence
)
from gieni_os.api.routes.opportunities import get_pof_html
from gieni_os.api.deps import get_current_user, ClerkUserContext
import uuid
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("gieni_os.api")

# Initialize database schema
init_db()

app = FastAPI(
    title="Gieni OS - Platform Operations API",
    description="Operating System Foundation: Counties, Cases, Workflows, Opportunities, Queues, and Human Review.",
    version="2.0.0"
)

class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = req_id
        start = time.perf_counter()
        logger.info("[%s] INBOUND %s %s", req_id, request.method, request.url.path)
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0
        response.headers["x-request-id"] = req_id
        logger.info("[%s] OUTBOUND %s %s -> status=%d (%.2f ms)", req_id, request.method, request.url.path, response.status_code, duration_ms)
        return response

app.add_middleware(RequestCorrelationMiddleware)

# Explicit CORS Origins Configuration
raw_origins = os.getenv("ALLOWED_ORIGIN") or os.getenv("ALLOWED_ORIGINS") or "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,http://127.0.0.1:3000"
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(counties.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(opportunities.router, prefix="/api")
app.include_router(workflow.router, prefix="/api")
app.include_router(exceptions.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ai_investigator.router, prefix="/api")
app.include_router(client_portal.router, prefix="/api")
app.include_router(ingestion.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(llm.router, prefix="/api")
app.include_router(intelligence.router, prefix="/api")

# Directory Paths
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
APPS_DIR = os.path.join(REPO_ROOT, "apps")
DASHBOARD_DIR = os.path.join(APPS_DIR, "dashboard")
LAUNCHPAD_DIR = os.path.join(APPS_DIR, "launchpad")
OPS_DIR = os.path.join(APPS_DIR, "ops-center")
WORKBENCH_DIR = os.path.join(APPS_DIR, "workbench")
INVESTIGATOR_DIR = os.path.join(APPS_DIR, "investigator")
PORTAL_DIR = os.path.join(APPS_DIR, "client-portal")
COUNTIES_DIR = os.path.join(APPS_DIR, "county-intelligence")

# Shared Static Assets (/static/css/style.css, etc.)
if os.path.exists(DASHBOARD_DIR):
    app.mount("/static", StaticFiles(directory=DASHBOARD_DIR), name="static")

# Mount App 1: Operations Center (/ops)
if os.path.exists(OPS_DIR):
    app.mount("/ops", StaticFiles(directory=OPS_DIR, html=True), name="ops_center")

# Mount App 2: Opportunity Workbench (/workbench)
if os.path.exists(WORKBENCH_DIR):
    app.mount("/workbench", StaticFiles(directory=WORKBENCH_DIR, html=True), name="workbench")

# Mount App 3: AI Investigator (/investigator)
if os.path.exists(INVESTIGATOR_DIR):
    app.mount("/investigator", StaticFiles(directory=INVESTIGATOR_DIR, html=True), name="investigator")

# Mount App 4: Client Portal (/portal)
if os.path.exists(PORTAL_DIR):
    app.mount("/portal", StaticFiles(directory=PORTAL_DIR, html=True), name="client_portal")

# Mount App 5: County Intelligence (/counties)
if os.path.exists(COUNTIES_DIR):
    app.mount("/counties", StaticFiles(directory=COUNTIES_DIR, html=True), name="county_intelligence")

# Route Handlers for Root & Clean Slash Navigation
@app.get("/")
def serve_launchpad():
    launchpad_file = os.path.join(LAUNCHPAD_DIR, "index.html")
    if os.path.exists(launchpad_file):
        return FileResponse(launchpad_file)
    ops_file = os.path.join(OPS_DIR, "index.html")
    if os.path.exists(ops_file):
        return FileResponse(ops_file)
    return {"message": "Gieni OS Enterprise Suite Active."}

@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "gieni-os-platform-api",
        "version": "2.0.0"
    }

@app.on_event("startup")
def validate_production_security():
    is_demo = os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes")
    if not is_demo:
        clerk_key = os.getenv("CLERK_PEM_PUBLIC_KEY") or os.getenv("CLERK_SECRET_KEY")
        if not clerk_key:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: CLERK_PEM_PUBLIC_KEY or CLERK_SECRET_KEY must be configured in production (DEMO_MODE=false)."
            )

# POF HTML direct route alias
@app.get("/api/pof/{opportunity_id}/html")
def pof_html_alias(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(get_current_user)
):
    return get_pof_html(opportunity_id=opportunity_id, db=db, user=user)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
