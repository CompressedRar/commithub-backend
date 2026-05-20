"""Add main_form_template_id to system_settings table

Revision ID: system_settings_form_template_001
Revises: 
Create Date: 2026-04-17 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'system_settings_form_template_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add main_form_template_id column to system_settings
    op.add_column('system_settings', sa.Column('main_form_template_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_system_settings_main_form_template_id',
        'system_settings',
        'form_templates',
        ['main_form_template_id'],
        ['id']
    )


def downgrade():
    # Drop foreign key
    op.drop_constraint('fk_system_settings_main_form_template_id', 'system_settings', type_='foreignkey')
    
    # Drop column
    op.drop_column('system_settings', 'main_form_template_id')
