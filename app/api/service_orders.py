from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.service_order_service import (
    ServiceOrderService,
)


router = APIRouter(
    prefix="/service-orders",
    tags=["Service Orders"],
)


@router.get("/{service_order_id}")
def get_service_order(
    service_order_id: int,
    db: Session = Depends(get_db),
):
    result = ServiceOrderService.get_service_order(
        db,
        service_order_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Service order not found",
        )

    return result


@router.get("/{service_order_id}/diagnostic")
def diagnose_service_order(
    service_order_id: int,
    db: Session = Depends(get_db),
):
    result = ServiceOrderService.diagnose(
        db,
        service_order_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Service order not found",
        )

    return result
