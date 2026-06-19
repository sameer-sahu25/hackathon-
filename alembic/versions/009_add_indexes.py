"""add additional performance indexes

Revision ID: 009_add_indexes
Revises: 008_create_analytics
Create Date: 2025-01-01 00:08:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009_add_indexes'
down_revision = '008_create_analytics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add full-text search index on resources.name
    op.execute('''
        CREATE INDEX idx_resources_fts_name ON resources 
        USING GIN (to_tsvector('english', name));
    ''')
    
    # Add BRIN index on analytics_events.created_at for time-range queries
    op.execute('''
        CREATE INDEX idx_analytics_brin_created_at ON analytics_events 
        USING BRIN (created_at);
    ''')
    
    # Add composite index on analytics_events for common query patterns
    op.create_index(
        'idx_analytics_event_date_state',
        'analytics_events',
        ['event_type', 'created_at', 'state'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_analytics_event_date_state', table_name='analytics_events')
    op.drop_index('idx_analytics_brin_created_at', table_name='analytics_events')
    op.drop_index('idx_resources_fts_name', table_name='resources')
