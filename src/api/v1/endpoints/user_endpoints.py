from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.db.database import get_db
from src.services.user_services import UserService
from src.schemas.user_schemas import (
    UserCreate, UserLogin, UserUpdate, AdminUserUpdate, 
    UserResponse
)
from src.db.dependencies import require_role
from src.db.models.user_model import User
from src.utils.auth_utils import get_current_user, create_access_token, create_refresh_token, RefreshTokenBearer

router = APIRouter(prefix="/users", tags=["Users"])

# ---------------- SIGNUP ----------------
@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db),using:User=Depends(require_role("TenantAdmin"))):
    service = UserService(db)
    new_user = await service.create_user(user)
    return new_user

# ---------------- LOGIN ----------------
@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    db_user = await service.authenticate_user(user.email, user.password)
    if not db_user or not db_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user_id=str(db_user.id), tenant_id=str(db_user.tenant_id))
    refresh_token = create_refresh_token(user_id=str(db_user.id), tenant_id=str(db_user.tenant_id))
    return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}


# ---------------- REFRESH TOKEN ----------------
@router.post("/refresh")
async def refresh_token(token_details: dict = Depends(RefreshTokenBearer())):
    user_id = token_details.get("sub")
    tenant_id = token_details.get("tenant_id")
    if not user_id or not tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    new_access_token = create_access_token(user_id=str(user_id), tenant_id=str(tenant_id))
    return {"access_token": new_access_token, "token_type": "bearer"}

# ---------------- GET ALL USERS (Tenant Scoped) ----------------
@router.get("/", response_model=list[UserResponse])
async def get_users(current_user: UserResponse = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    users = await service.get_all_users(current_user.tenant_id)
    return users

# ---------------- UPDATE USER (Normal User) ----------------
@router.put("/me", response_model=UserResponse)
async def update_me(user_update: UserUpdate,
                    current_user: UserResponse = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    updated_user = await service.update_user(current_user.id, current_user.tenant_id, user_update)
    return updated_user

# ---------------- ADMIN UPDATE USER ----------------
@router.put("/{user_id}", response_model=UserResponse)
async def admin_update_user(user_id: UUID, user_update: AdminUserUpdate,
                            current_user: UserResponse = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update other users")
    service = UserService(db)
    updated_user = await service.admin_update_user(user_id, current_user.tenant_id, user_update)
    return updated_user

# ---------------- DELETE USER (Soft Delete) ----------------
@router.delete("/{user_id}")
async def delete_user(user_id: UUID,
                      current_user: UserResponse = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete users")
    service = UserService(db)
    result = await service.delete_user(user_id, current_user.tenant_id)
    return result