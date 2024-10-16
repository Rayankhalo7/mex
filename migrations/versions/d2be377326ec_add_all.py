"""Add all

Revision ID: d2be377326ec
Revises: 7bba9df2e543
Create Date: 2024-10-18 12:29:21.704946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2be377326ec'
down_revision = '7bba9df2e543'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.add_column(sa.Column('city_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'cities', ['city_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('city_id')

    # ### end Alembic commands ###
