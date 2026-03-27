from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, date
from pydantic import model_validator
from enum import Enum
from src.db.models.user_model import User


class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class LeaveType(str,Enum):
    SICK="sick"
    CASUAL="casual"
    EARNED="earned"
    UNPAID="unpaid"    


class LeaveRequest(SQLModel, table=True):
    __tablename__ = "leave_requests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    user_id: UUID = Field(foreign_key="users.id", index=True)

    leave_type: LeaveType =Field(nullable=False,index=True)

    start_date: date
    end_date: date

    reason: Optional[str] = None

    status: LeaveStatus = Field(default=LeaveStatus.PENDING, index=True)

    approved_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    rejected_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow,
                                 sa_column_kwargs={"onupdate":datetime.utcnow})

    user: Optional["User"] = Relationship(
    back_populates="leave_requests",
      sa_relationship_kwargs={"foreign_keys": "[LeaveRequest.user_id]"}
    )
     
    approver: Optional["User"] = Relationship(
      sa_relationship_kwargs={"foreign_keys": "[LeaveRequest.approved_by]"}
    )
    rejector: Optional["User"] = Relationship(
    sa_relationship_kwargs={"foreign_keys": "[LeaveRequest.rejected_by]"}
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self

    @property
    def total_days(self) -> int:
        return (self.end_date - self.start_date).days + 1