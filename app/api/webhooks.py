from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/retell")
async def retell_webhook(
    payload: dict,
    db: Session = Depends(get_db)
):
    print(payload)