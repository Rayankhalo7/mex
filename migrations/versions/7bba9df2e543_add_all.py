"""Add all

Revision ID: 7bba9df2e543
Revises: 264744b3e0eb
Create Date: 2024-10-18 12:29:09.386161

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7bba9df2e543'
down_revision = '264744b3e0eb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.drop_constraint('client_ibfk_1', type_='foreignkey')
        batch_op.drop_column('city_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.add_column(sa.Column('city_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False))
        batch_op.create_foreign_key('client_ibfk_1', 'cities', ['city_id'], ['id'])

    # ### end Alembic commands ###