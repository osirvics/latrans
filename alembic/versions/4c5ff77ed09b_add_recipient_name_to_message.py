"""Add recipient name to message

Revision ID: 4c5ff77ed09b
Revises: abda1eb7b60e
Create Date: 2017-11-18 21:46:44.143408

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c5ff77ed09b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
	op.add_column('message', sa.Column('recipient_first_name', sa.Text))
	op.add_column('message', sa.Column('recipient_last_name', sa.Text))
    


def downgrade():
	op.drop_column('message', sa.Column('recipient_first_name', sa.Text))
	op.drop_column('message', sa.Column('recipient_last_name', sa.Text))
    
