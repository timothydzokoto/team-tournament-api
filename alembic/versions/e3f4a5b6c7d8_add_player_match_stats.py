"""Add player_match_stats table

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-04-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e3f4a5b6c7d8'
down_revision = 'd2e3f4a5b6c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'player_match_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('goals', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assists', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('yellow_cards', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('red_cards', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('minutes_played', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id']),
        sa.ForeignKeyConstraint(['player_id'], ['players.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('match_id', 'player_id', name='uq_player_match_stat'),
    )
    op.create_index(op.f('ix_player_match_stats_id'), 'player_match_stats', ['id'], unique=False)
    op.create_index(op.f('ix_player_match_stats_match_id'), 'player_match_stats', ['match_id'], unique=False)
    op.create_index(op.f('ix_player_match_stats_player_id'), 'player_match_stats', ['player_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_player_match_stats_player_id'), table_name='player_match_stats')
    op.drop_index(op.f('ix_player_match_stats_match_id'), table_name='player_match_stats')
    op.drop_index(op.f('ix_player_match_stats_id'), table_name='player_match_stats')
    op.drop_table('player_match_stats')
