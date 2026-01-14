"""added admin_confirmations table

Revision ID: a9f8c7b6d5e4
Revises: 052ae3da1dbc
Create Date: 2026-01-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a9f8c7b6d5e4'
down_revision = '052ae3da1dbc'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'admin_confirmations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token', sa.String(length=128), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('admin_confirmations')
