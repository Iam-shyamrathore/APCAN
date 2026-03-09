"""Add FHIR resources - Encounter, Appointment, Observation

Revision ID: 002_add_fhir_resources
Revises: 001_initial_migration
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_fhir_resources'
down_revision: Union[str, None] = '001_initial_migration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create encounters table
    op.create_table(
        'encounters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('provider_id', sa.Integer(), nullable=True),
        sa.Column('encounter_class', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reason_code', sa.String(length=100), nullable=True),
        sa.Column('reason_display', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_encounters_patient_id', 'encounters', ['patient_id'])
    op.create_index('ix_encounters_provider_id', 'encounters', ['provider_id'])
    op.create_index('ix_encounters_period_start', 'encounters', ['period_start'])
    
    # Create appointments table
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('provider_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('appointment_type', sa.String(length=100), nullable=True),
        sa.Column('service_category', sa.String(length=100), nullable=True),
        sa.Column('start_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_appointments_patient_id', 'appointments', ['patient_id'])
    op.create_index('ix_appointments_provider_id', 'appointments', ['provider_id'])
    op.create_index('ix_appointments_status', 'appointments', ['status'])
    op.create_index('ix_appointments_start_datetime', 'appointments', ['start_datetime'])
    
    # Create observations table
    op.create_table(
        'observations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('display', sa.Text(), nullable=False),
        sa.Column('value_quantity', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('value_unit', sa.String(length=50), nullable=True),
        sa.Column('value_string', sa.Text(), nullable=True),
        sa.Column('reference_range_low', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('reference_range_high', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('effective_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('issued', sa.DateTime(timezone=True), nullable=True),
        sa.Column('interpretation', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_observations_patient_id', 'observations', ['patient_id'])
    op.create_index('ix_observations_encounter_id', 'observations', ['encounter_id'])
    op.create_index('ix_observations_category', 'observations', ['category'])
    op.create_index('ix_observations_code', 'observations', ['code'])
    op.create_index('ix_observations_effective_datetime', 'observations', ['effective_datetime'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index('ix_observations_effective_datetime', table_name='observations')
    op.drop_index('ix_observations_code', table_name='observations')
    op.drop_index('ix_observations_category', table_name='observations')
    op.drop_index('ix_observations_encounter_id', table_name='observations')
    op.drop_index('ix_observations_patient_id', table_name='observations')
    op.drop_table('observations')
    
    op.drop_index('ix_appointments_start_datetime', table_name='appointments')
    op.drop_index('ix_appointments_status', table_name='appointments')
    op.drop_index('ix_appointments_provider_id', table_name='appointments')
    op.drop_index('ix_appointments_patient_id', table_name='appointments')
    op.drop_table('appointments')
    
    op.drop_index('ix_encounters_period_start', table_name='encounters')
    op.drop_index('ix_encounters_provider_id', table_name='encounters')
    op.drop_index('ix_encounters_patient_id', table_name='encounters')
    op.drop_table('encounters')
