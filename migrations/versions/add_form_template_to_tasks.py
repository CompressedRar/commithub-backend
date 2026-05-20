"""Add form_template_id to main_tasks table

Revision ID: form_template_tasks_001
Revises: 
Create Date: 2026-04-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'form_template_tasks_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add form_template_id column to main_tasks
    op.add_column('main_tasks', sa.Column('form_template_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_main_tasks_form_template_id',
        'main_tasks',
        'form_templates',
        ['form_template_id'],
        ['id']
    )


def downgrade():
    # Drop foreign key
    op.drop_constraint('fk_main_tasks_form_template_id', 'main_tasks', type_='foreignkey')
    
    # Drop column
    op.drop_column('main_tasks', 'form_template_id')
