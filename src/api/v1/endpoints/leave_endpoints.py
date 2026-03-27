from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from src.db.database import async_session
from src.services.leave_services import LeaveServices
from src.db.models.user_model import User
from src.schemas.LeaveReq_schema import LeaveRequestCreate, LeaveRequestRead
from src.schemas.LeaveBalance_schema import LeaveBalanceRead
from src.utils.auth_utils import get_current_user
from src.db.database import get_db

router = APIRouter(
    prefix="/leaves",
    tags=["Leaves"]
)

@router.post("/apply_leave", response_model=LeaveRequestRead)
async def apply_leave(
    leave_data: LeaveRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LeaveServices(db)
    try:
        leave = await service.apply_leave(
            user_id=current_user.id,
            leave_type=leave_data.leave_type,
            start_date=leave_data.start_date,
            end_date=leave_data.end_date,
            reason=leave_data.reason
        )
        return leave
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.get("/balance", response_model=LeaveBalanceRead)
async def get_my_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LeaveServices(db)
    balance = await service.get_my_leave_balance(current_user.id)
    if not balance:
        raise HTTPException(status_code=404, detail="Leave balance not found")
    return balance

@router.get("/my-requests", response_model=List[LeaveRequestRead])
async def my_leave_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LeaveServices(db)
    requests = await service.get_leave_requests(current_user)
    return requests


@router.patch("/{leave_id}/approve", response_model=LeaveRequestRead)
async def approve_leave(
    leave_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LeaveServices(db)
    try:
        leave = await service.approve_leave(leave_id, current_user)
        return leave
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.patch("/{leave_id}/reject", response_model=LeaveRequestRead)
async def reject_leave(
    leave_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LeaveServices(db)
    try:
        leave = await service.reject_leave(leave_id, current_user)
        return leave
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.get("/all", response_model=List[LeaveRequestRead])
async def all_leave_requests(
    tenant_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LeaveServices(db)
    if current_user.role != "HR":
        raise HTTPException(status_code=403, detail="Not authorized")
    requests = await service.get_leave_requests(current_user, tenant_only=tenant_only)
    return requests

@router.get("/balances", response_model=List[LeaveBalanceRead])
async def all_leave_balances(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LeaveServices(db)
    try:
        balances = await service.get_all_leave_balance(current_user)
        return balances
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))