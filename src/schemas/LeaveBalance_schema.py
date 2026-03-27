from pydantic import BaseModel
from uuid import UUID


class LeaveBalanceRead(BaseModel):
    user_id: UUID
    year: int

    sick_total: int
    sick_used: int
    remaining_sick: int

    casual_total: int
    casual_used: int
    remaining_casual: int

    earned_total: int
    earned_used: int
    earned_carry_forward: int
    remaining_earned: int

    unpaid_taken: int

    class Config:
        from_attributes = True