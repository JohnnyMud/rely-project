from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CallAttempts

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/retell", status_code=status.HTTP_200_OK)
async def retell_webhook(
    payload: dict,
    db: Session = Depends(get_db)
):
    return {"message": "Webhook received"}