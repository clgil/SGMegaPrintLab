"""Auditoría: tabla audit_log (bitácora inmutable anti-fraude)

Migración enfocada y revisada manualmente: SOLO crea la tabla `audit_log`
y sus índices. No toca las demás tablas para no arrastrar ruido de
autogeneración (reconstrucciones batch de SQLite con tipos TEXT nativos).

Revision ID: b7c31d92e4a1
Revises: 112a730df0d5
Create Date: 2026-10-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c31d92e4a1'
down_revision = '112a730df0d5'
branch_labels = None
depends_on = None


def upgrade():
    # ### Bitácora de auditoría (append-only, solo lectura desde la UI) ###
    op.create_table('audit_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('username', sa.Text(), nullable=True),
    sa.Column('action', sa.Text(), nullable=False),
    sa.Column('table_name', sa.Text(), nullable=False),
    sa.Column('record_id', sa.Text(), nullable=True),
    sa.Column('old_values', sa.Text(), nullable=True),
    sa.Column('new_values', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('ip_address', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'],
                            name=op.f('fk_audit_log_user_id_usuarios')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_log'))
    )
    # Índices para los filtros de /admin/auditoria (usuario, tabla, fechas)
    op.create_index(op.f('ix_audit_log_timestamp'), 'audit_log', ['timestamp'])
    op.create_index(op.f('ix_audit_log_username'), 'audit_log', ['username'])
    op.create_index(op.f('ix_audit_log_table_name'), 'audit_log', ['table_name'])


def downgrade():
    op.drop_index(op.f('ix_audit_log_table_name'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_username'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_timestamp'), table_name='audit_log')
    op.drop_table('audit_log')
