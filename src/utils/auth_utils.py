from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from uuid import UUID
from src.core.config import config 
from src.core.security import hash_password as _hash_password, verify_password as _verify_password
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.database import get_db
if TYPE_CHECKING:
    from src.services.user_services import UserService
from src.schemas.user_schemas import UserResponse



bearer_scheme = HTTPBearer()


# ---------------- CREATE ACCESS TOKEN ----------------
def create_access_token(
    user_id: str,
    tenant_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = {"sub": user_id, "type": "access"}
    if tenant_id is not None:
        to_encode["tenant_id"] = tenant_id
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return token


def create_refresh_token(
    user_id: str,
    tenant_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = {"sub": user_id, "tenant_id": tenant_id, "type": "refresh"}
    expire = datetime.utcnow() + (expires_delta or timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return token


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except JWTError:
        return None


class RefreshTokenBearer:
    def __init__(self):
        self._scheme = HTTPBearer()

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> dict:
        token = credentials.credentials
        payload = decode_token(token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        return payload


def generate_password_hash(password: str) -> str:
    return _hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _verify_password(plain_password, hashed_password)


# ---------------- GET CURRENT USER ----------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db)
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        if payload.get("type") == "refresh":
            raise credentials_exception
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        if user_id is None or tenant_id is None:
            raise credentials_exception
        user_id = UUID(user_id)
        tenant_id = UUID(tenant_id)
    except JWTError:
        raise credentials_exception

    from src.services.user_services import UserService  
    service = UserService(session)
    user = await service.get_user_by_id(user_id, tenant_id)
    if not user or not user.is_active:
        raise credentials_exception

    return UserResponse.from_orm(user)