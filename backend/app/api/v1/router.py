from fastapi import APIRouter
from app.api.v1.cases import router as cases_router
from app.api.v1.opportunities import router as opps_router
from app.api.v1.exceptions import router as exceptions_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.ai import router as ai_router
from app.api.v1.telemetry import router as telemetry_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(cases_router)
api_v1_router.include_router(opps_router)
api_v1_router.include_router(exceptions_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(telemetry_router)
