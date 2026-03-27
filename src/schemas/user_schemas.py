from pydantic import BaseModel, EmailStr,Field
from typing import Optional ,Literal
import uuid


# ---------------- CREATE (Public Signup) ----------------
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str = Field(min_length=4)
    tenant_id: uuid.UUID
    invite_code: str
    role: str = "employee"


# ---------------- LOGIN ----------------
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ---------------- UPDATE ----------------
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None,min_length=4)
 


# ---------------- ADMIN UPDATE (optional but recommended) ----------------
class AdminUserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None,min_length=4)
    role: Optional[Literal["employee", "manager", "admin"]] = None
    is_active: Optional[bool] = None   #can deactivate the user  instead of deleting the user from the database

# ---------------- RESPONSE ----------------
class UserResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    role: str
    tenant_id: uuid.UUID
    is_active: bool

    class Config:
        from_attributes = True