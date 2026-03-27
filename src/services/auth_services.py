# services/auth_services.py
from uuid import UUID
from datetime import timedelta

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from src.services.user_services import UserService
from src.utils.auth_utils import verify_password, create_access_token, decode_token

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def login(self, email: str, password: str):
        user = await self.user_service.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token(user_id=str(user.id))
        return {"access_token": access_token, "token_type": "bearer"}

   
    async def require_admin(self, user):
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")