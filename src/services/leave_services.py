from src.db.database import AsyncSession
from src.db.models.leaverequest_model import LeaveRequest,LeaveStatus,LeaveType
from src.db.models.leavebalance_model import LeaveBalance
from src.db.models.user_model import User
from uuid import UUID
from datetime import date,datetime
from sqlalchemy import select ,func
class LeaveServices:
    def __init__(self,db:AsyncSession):
        self.db=db


#  showing the leave balance 
    async def get_my_leave_balance(self,user_id:UUID):
        result = await self.db.execute(
            select(LeaveBalance).where(LeaveBalance.user_id==user_id)
        )   
        return result.scalar_one_or_none()
    
#  for hr to check the  all employee leaves
    async def get_all_leave_balance(self,current_user:User):
        if current_user.role!="HR":
            raise PermissionError("Not Authorized")
        result=await self.db.execute(
            select(LeaveBalance).join(User).where(User.tenant_id == current_user.tenant_id)
        )
        return result.scalars().all()



    # -----------------------------
    # Leave Request Operations
    # -----------------------------
    async def apply_leave(self, user_id: UUID, leave_type: LeaveType, start_date: date,
                          end_date: date, reason: str = None):
        
        total_days = (end_date - start_date).days + 1
        if total_days <= 0:
            raise ValueError("Leave must be at least 1 day")

        # Fetch leave balance for the year
        result = await self.db.execute(
            select(LeaveBalance).where(
                LeaveBalance.user_id == user_id,
                LeaveBalance.year == start_date.year
            )
        )
        balance = result.scalar_one_or_none()
        if not balance:
            raise ValueError("Leave balance not found for this user/year")

        # Check monthly limits for sick and casual leaves
        if leave_type in [LeaveType.SICK, LeaveType.CASUAL]:
            month_start = date(start_date.year, start_date.month, 1)
            month_end = date(start_date.year, start_date.month, 31)
            month_count = await self.db.scalar(
                select(func.count(LeaveRequest.id)).where(
                    LeaveRequest.user_id == user_id,
                    LeaveRequest.leave_type == leave_type,
                    LeaveRequest.status == LeaveStatus.APPROVED,
                    LeaveRequest.start_date >= month_start,
                    LeaveRequest.start_date <= month_end
                )
            )
            if month_count >= 1:
                # Convert to earned leave
                leave_type = LeaveType.EARNED

        # Create leave request with PENDING status
        leave_request = LeaveRequest(
            user_id=user_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status=LeaveStatus.PENDING
        )
        self.db.add(leave_request)
        await self.db.commit()
        await self.db.refresh(leave_request)
        return leave_request

    async def approve_leave(self, leave_request_id: UUID, approver: User):
        """HR approves leave request"""
        if approver.role != "HR":
            raise PermissionError("Not authorized")

        result = await self.db.execute(
            select(LeaveRequest).where(LeaveRequest.id == leave_request_id)
        )
        leave = result.scalar_one_or_none()
        if not leave:
            raise ValueError("Leave request not found")

        leave.approved_by = approver.id
        leave.status = LeaveStatus.APPROVED

        # Update leave balance
        result = await self.db.execute(
            select(LeaveBalance).where(
                LeaveBalance.user_id == leave.user_id,
                LeaveBalance.year == leave.start_date.year
            )
        )
        balance = result.scalar_one_or_none()
        if not balance:
            raise ValueError("Leave balance not found")

        # Deduct the leave based on type
        total_days = (leave.end_date - leave.start_date).days + 1
        if leave.leave_type == LeaveType.SICK:
            balance.sick_used += total_days
        elif leave.leave_type == LeaveType.CASUAL:
            balance.casual_used += total_days
        elif leave.leave_type == LeaveType.EARNED:
            balance.earned_used += total_days
        elif leave.leave_type == LeaveType.UNPAID:
            balance.unpaid_taken += total_days

        await self.db.commit()
        await self.db.refresh(leave)
        return leave

    async def reject_leave(self, leave_request_id: UUID, approver: User):
        """HR rejects leave request"""
        if approver.role != "HR":
            raise PermissionError("Not authorized")

        result = await self.db.execute(
            select(LeaveRequest).where(LeaveRequest.id == leave_request_id)
        )
        leave = result.scalar_one_or_none()
        if not leave:
            raise ValueError("Leave request not found")

        leave.approved_by = approver.id
        leave.status = LeaveStatus.REJECTED
        await self.db.commit()
        await self.db.refresh(leave)
        return leave

    async def get_leave_requests(self, user: User, tenant_only: bool = False):

          query = select(LeaveRequest)
      
          if user.role == "HR":
              query = query.join(LeaveRequest.user).where(
                  User.tenant_id == user.tenant_id
              )
          else:
              query = query.where(LeaveRequest.user_id == user.id)
      
          result = await self.db.execute(query)
          return result.scalars().all()