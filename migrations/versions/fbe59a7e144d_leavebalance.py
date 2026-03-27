from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = 'fbe59a7e144d'
down_revision: Union[str, Sequence[str], None] = '6c20c8b1a7e3'
branch_labels = None
depends_on = None


def table_exists(table_name: str, schema: str = None) -> bool:
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names(schema=schema)


def create_schema_if_not_exists(schema_name: str):
    conn = op.get_bind()
    conn.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))


def upgrade() -> None:
    schema_name = "public"  # change if needed (e.g., "hr")

    # ✅ create schema (optional)
    create_schema_if_not_exists(schema_name)

    # ✅ check table existence
    if not table_exists("leave_balances", schema=schema_name):
        op.create_table(
            'leave_balances',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('total_leaves', sa.Integer(), nullable=False),
            sa.Column('used_leaves', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            schema=schema_name   # 👈 IMPORTANT
        )


def downgrade() -> None:
    schema_name = "public"

    if table_exists("leave_balances", schema=schema_name):
        op.drop_table('leave_balances', schema=schema_name)