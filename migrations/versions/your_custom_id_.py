"""empty message

Revision ID: your_custom_id
Revises: 1ba29fe94aa3
Create Date: 2024-10-18 12:22:36.348696

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'your_custom_id'
down_revision = '1ba29fe94aa3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'cities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=False, unique=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('postal_code')
    )


def downgrade():
    pass
