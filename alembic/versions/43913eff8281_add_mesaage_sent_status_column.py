"""Add mesaage sent status column

Revision ID: 43913eff8281
Revises: 
Create Date: 2017-09-30 21:05:36.814335

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43913eff8281'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
	op.add_column('message', sa.Column('sent_status', sa.Text))
    

def downgrade():
	op.drop_column('message', 'sent_status')
    
