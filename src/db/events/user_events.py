from sqlalchemy import event
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import insert
from src.db.models.user_model import User
from src.db.models.leavebalance_model import LeaveBalance

@event.listens_for(User,"after_insert")
def create_leave_balance(mapper,connection,target):
    """
    Automatically create leave balance when a new user is created
    """
    current_year=datetime.utcnow().year
    stmt = insert(LeaveBalance).values(
        id=uuid.uuid4(),
        user_id=target.id,
        year =current_year,
        sick_total =12,
        sick_used=0,
        casual_total=12,
        casual_used=0,
        earned_total=10,
        earned_used =0,
        earned_carry_forward=0,
        unpaid_taken=0
 )
    stmt=stmt.on_conflict_do_nothing(
        index_elements=["user_id","year"]
    )
    connection.execute(stmt)