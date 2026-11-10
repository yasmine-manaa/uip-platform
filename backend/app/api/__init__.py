from fastapi import APIRouter
from app.api.cases import router as cases_router
from app.api.documents import router as documents_router
from app.api.analysis import router as analysis_router
from app.api.reviews import router as reviews_router
from app.api.audit import router as audit_router
from app.api.benchmarks import router as benchmarks_router
from app.api.system import router as system_router
from app.api.clients import router as clients_router
from app.api.dataset import router as dataset_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(cases_router)
api_router.include_router(documents_router)
api_router.include_router(analysis_router)
api_router.include_router(reviews_router)
api_router.include_router(audit_router)
api_router.include_router(benchmarks_router)
api_router.include_router(system_router)
api_router.include_router(clients_router)
api_router.include_router(dataset_router)

__all__ = ["api_router"]
