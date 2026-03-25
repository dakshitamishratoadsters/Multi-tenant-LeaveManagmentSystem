from sqlmodel import SQLModel,Field,Relationship,UniqueConstraint
from typing import Optional,List
from uuid import UUID,uuid4

from src.db.models.user_model import User
from src.db.models.leaverequest_model import LeaveRequest


class LeaveBalance(SQLModel,table=True):
    __tablename__="leave_balances"
    __table_args__=(UniqueConstraint("user_id","year"),)

    id:UUID = Field(default_factory=uuid4,primary_key=True)
    user_id:UUID = Field(foreign_key ="users.id",nullable=False)
    year:int= Field(nullable=False)
    # Sick Leaves
    sick_total: int = Field(default=12, nullable=False)
    sick_used: int = Field(default=0,nullable=False)

    # Casual Leaves
    casual_total:int = Field(default=12,nullable=False)
    casual_used: int = Field(default=0,nullable=False)

    # Earned Leaves
    earned_total:int = Field(default=10, nullable=False)
    earned_used:int = Field(default=0,nullable=False)
    earned_carry_forward:int = Field(default=0,nullable=False)

     #  Unpaid Leaves 
    unpaid_taken: int = Field(default=0, nullable=False)

    user: Optional["User"] = Relationship(back_populates="leave_balances")

    #  Remaining Calculations
    @property
    def remaining_sick(self) -> int:
        return self.sick_total - self.sick_used

    @property
    def remaining_casual(self) -> int:
        return self.casual_total - self.casual_used

    @property
    def remaining_earned(self) -> int:
        return (self.earned_total + self.earned_carry_forward) - self.earned_used
