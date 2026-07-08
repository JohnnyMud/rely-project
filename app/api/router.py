from fastapi import APIRouter

from .patient_records import router as patients_router
from .calls import router as calls_router
from .webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(patients_router)
api_router.include_router(calls_router)
api_router.include_router(webhooks_router)