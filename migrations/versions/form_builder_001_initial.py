"""Add form builder tables

Revision ID: form_builder_001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'form_builder_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create form_templates table
    op.create_table(
        'form_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('subtitle', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('grid_rows', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('grid_columns', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('field_mapping', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_published', sa.Boolean(), nullable=True, server_default='false'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create form_input_fields table
    op.create_table(
        'form_input_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('placeholder', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('field_type', sa.String(length=50), nullable=False),
        sa.Column('user_type', sa.String(length=50), nullable=True, server_default='Admin'),
        sa.Column('is_required', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('validation_rules', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['form_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create form_output_fields table
    op.create_table(
        'form_output_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('output_type', sa.String(length=50), nullable=False),
        sa.Column('input_field_name', sa.String(length=100), nullable=True),
        sa.Column('formula', sa.Text(), nullable=True),
        sa.Column('cases', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['form_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create form_submissions table
    op.create_table(
        'form_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('submitted_by', sa.Integer(), nullable=False),
        sa.Column('submission_date', sa.DateTime(), nullable=True),
        sa.Column('is_draft', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['form_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create form_field_values table
    op.create_table(
        'form_field_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('input_field_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['input_field_id'], ['form_input_fields.id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['form_submissions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop tables in reverse order of creation
    op.drop_table('form_field_values')
    op.drop_table('form_submissions')
    op.drop_table('form_output_fields')
    op.drop_table('form_input_fields')
    op.drop_table('form_templates')
