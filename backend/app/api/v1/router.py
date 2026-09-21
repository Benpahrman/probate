from fastapi import APIRouter
from app.api.v1.cases import router as cases_router
from app.api.v1.opportunities import router as opps_router
from app.api.v1.exceptions import router as exceptions_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(cases_router)
api_v1_router.include_router(opps_router)
api_v1_router.include_router(exceptions_router)
