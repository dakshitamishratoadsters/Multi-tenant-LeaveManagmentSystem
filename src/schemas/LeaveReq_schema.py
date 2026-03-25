from pydantic import BaseModel ,model_validator
from datetime import date , datetime
from typing import Optional ,List
from uuid import UUID
from src.db.models.leaverequest_model import LeaveType,LeaveStatus

class LeaveRequestCreate(BaseModel):
    leave_type:LeaveType
    start_date:date
    end_date:date
    reason:Optional[str]

    @model_validator(mode='after')
    def validate_dates(self):
        if self.end_date <self.start_date:
            raise ValueError("end_date  can not be  before start_date")
        return self


class LeaveRequestUpdate(BaseModel):
    status:LeaveStatus   
    approved_by:UUID

class LeaveRequestRead(BaseModel):
    id:UUID
    user_id:UUID
    leave_type:LeaveType
    start_date:date
    end_date:date
    reason:Optional[str]
    status:LeaveStatus
    approved_by:Optional[UUID]
    created_at:datetime
    updated_at:datetime
    total_days:int

    class Config:
        from_attributes=True



class LeaveRequestListResponse(BaseModel):
    data: List[LeaveRequestRead]

