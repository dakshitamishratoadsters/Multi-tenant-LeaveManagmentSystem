from src.db.database import AsyncSession
from src.db.models.leaverequest_model import LeaveRequest, LeaveStatus, LeaveType
from src.db.models.leavebalance_model import LeaveBalance
from src.db.models.user_model import User
from uuid import UUID
from datetime import date
from sqlalchemy import select, func
import calendar


class LeaveServices:
    def __init__(self, db: AsyncSession):
        self.db = db

    # showing the leave balance
    async def get_my_leave_balance(self, user_id: UUID):
        result = await self.db.execute(
            select(LeaveBalance).where(LeaveBalance.user_id == user_id)
        )
        return result.scalar_one_or_none()

    # for hr to check all employee leaves
    async def get_all_leave_balance(self, current_user: User):
        if current_user.role != "HR":
            raise PermissionError("Not Authorized")

        result = await self.db.execute(
            select(LeaveBalance)
            .join(User, LeaveBalance.user_id == User.id)
            .where(User.tenant_id == current_user.tenant_id)
        )
        return result.scalars().all()

    # -----------------------------
    # Leave Request Operations
    # -----------------------------
    async def apply_leave(
        self,
        user_id: UUID,
        leave_type: LeaveType,
        start_date: date,
        end_date: date,
        reason: str = None
    ):
        try:
            total_days = (end_date - start_date).days + 1
            if total_days <= 0:
                raise ValueError("Leave must be at least 1 day")

            # overlap check
            overlap = await self.db.execute(
                select(LeaveRequest).where(
                    LeaveRequest.user_id == user_id,
                    LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
                    LeaveRequest.start_date <= end_date,
                    LeaveRequest.end_date >= start_date
                )
            )

            if overlap.scalars().first():
                raise ValueError("Overlapping leave request exists")

            # Fetch leave balance
            result = await self.db.execute(
                select(LeaveBalance).where(
                    LeaveBalance.user_id == user_id,
                    LeaveBalance.year == start_date.year
                )
            )
            balance = result.scalar_one_or_none()

            if not balance:
                raise ValueError("Leave balance not found for this user/year")

            # ✅ Balance check at APPLY TIME (FIXED)
            if leave_type == LeaveType.SICK:
                if balance.sick_used + total_days > balance.sick_total:
                    raise ValueError("Insufficient sick leave")

            elif leave_type == LeaveType.CASUAL:
                if balance.casual_used + total_days > balance.casual_total:
                    raise ValueError("Insufficient casual leave")

            elif leave_type == LeaveType.EARNED:
                if balance.earned_used + total_days > balance.earned_total:
                    raise ValueError("Insufficient earned leave")

            # monthly limit check (IMPROVED - still simple)
            if leave_type in [LeaveType.SICK, LeaveType.CASUAL]:
                month_start = date(start_date.year, start_date.month, 1)
                last_day = calendar.monthrange(start_date.year, start_date.month)[1]
                month_end = date(start_date.year, start_date.month, last_day)

                month_days = await self.db.scalar(
                    select(func.sum(
                        (LeaveRequest.end_date - LeaveRequest.start_date) + 1
                    )).where(
                        LeaveRequest.user_id == user_id,
                        LeaveRequest.leave_type == leave_type,
                        LeaveRequest.status == LeaveStatus.APPROVED,
                        LeaveRequest.start_date >= month_start,
                        LeaveRequest.start_date <= month_end
                    )
                )

                if month_days and (month_days + total_days > 2):  # assume 2 days/month
                    raise ValueError("Monthly leave limit exceeded")

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

        except Exception:
            await self.db.rollback()
            raise

    async def approve_leave(self, leave_request_id: UUID, approver: User):
       if approver.role != "HR":
           raise PermissionError("Not authorized")
   
       try:
           # Fetch leave request
           result = await self.db.execute(
               select(LeaveRequest)
               .join(User, LeaveRequest.user_id == User.id)
               .where(
                   LeaveRequest.id == leave_request_id,
                   User.tenant_id == approver.tenant_id
               )
           )
           leave = result.scalar_one_or_none()
           if not leave:
               raise ValueError("Leave request not found or not accessible")
           if leave.status != LeaveStatus.PENDING:
               raise ValueError("Leave already processed")
   
           # Overlap check
           result = await self.db.execute(
               select(LeaveRequest).where(
                   LeaveRequest.user_id == leave.user_id,
                   LeaveRequest.status == LeaveStatus.APPROVED,
                   LeaveRequest.end_date >= leave.start_date,
                   LeaveRequest.start_date <= leave.end_date,
               )
           )
           overlap = result.scalar_one_or_none()
           if overlap:
               raise ValueError("Leave dates overlap with existing approved leave")
   
           # Fetch balance
           result = await self.db.execute(
               select(LeaveBalance).where(
                   LeaveBalance.user_id == leave.user_id,
                   LeaveBalance.year == leave.start_date.year
               )
           )
           balance = result.scalar_one_or_none()
           if not balance:
               raise ValueError("Leave balance not found")
   
           total_days = (leave.end_date - leave.start_date).days + 1
   
           # Negative balance check
           if leave.leave_type == LeaveType.SICK:
               if balance.remaining_sick < total_days:
                   raise ValueError("Not enough sick leave balance")
               balance.sick_used += total_days
           elif leave.leave_type == LeaveType.CASUAL:
               if balance.remaining_casual < total_days:
                   raise ValueError("Not enough casual leave balance")
               balance.casual_used += total_days
           elif leave.leave_type == LeaveType.EARNED:
               if balance.remaining_earned < total_days:
                   raise ValueError("Not enough earned leave balance")
               balance.earned_used += total_days
           elif leave.leave_type == LeaveType.UNPAID:
               balance.unpaid_taken += total_days
   
           # Approve leave
           leave.status = LeaveStatus.APPROVED
           leave.approved_by = approver.id
           leave.rejected_by = None
   
           await self.db.commit()
           await self.db.refresh(leave)
           return leave
   
       except Exception:
           await self.db.rollback()
           raise
       
       
    # reject leave
    async def reject_leave(self, leave_request_id: UUID, approver: User):
        if approver.role != "HR":
            raise PermissionError("Not authorized")

        try:
            result = await self.db.execute(
                select(LeaveRequest)
                .join(User, LeaveRequest.user_id == User.id)
                .where(
                    LeaveRequest.id == leave_request_id,
                    User.tenant_id == approver.tenant_id
                )
            )
            leave = result.scalar_one_or_none()

            if not leave:
                raise ValueError("Leave request not found or not accessible")

            if leave.status != LeaveStatus.PENDING:
                raise ValueError("Leave already processed")

            leave.rejected_by = approver.id
            leave.approved_by = None
            leave.status = LeaveStatus.REJECTED

            await self.db.commit()
            await self.db.refresh(leave)

            return leave

        except Exception:
            await self.db.rollback()
            raise

    async def get_leave_requests(self, user: User):
        query = select(LeaveRequest)

        if user.role == "HR":
            query = query.join(User, LeaveRequest.user_id == User.id).where(
                User.tenant_id == user.tenant_id
            )
        else:
            query = query.where(LeaveRequest.user_id == user.id)

        # ✅ Added sorting (FIXED)
        query = query.order_by(LeaveRequest.start_date.desc())

        result = await self.db.execute(query)
        return result.scalars().all()