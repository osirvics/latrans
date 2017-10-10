"""edit request table

Revision ID: abda1eb7b60e
Revises: 43913eff8281
Create Date: 2017-10-08 17:36:59.138672

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abda1eb7b60e'
down_revision = '43913eff8281'
branch_labels = None
depends_on = None


def upgrade():
	op.add_column('request', sa.Column('phone_no', sa.Text))
	op.add_column('request', sa.Column('item_name', sa.Text))
	op.add_column('request', sa.Column('profile_image', sa.Text))
	op.add_column('request', sa.Column('user_first_name', sa.Text))
	op.add_column('request', sa.Column('user_last_name', sa.Text))
    
def downgrade():
	op.drop_column('request', sa.Column('phone_no', sa.Text))
	op.drop_column('request', sa.Column('item_name', sa.Text))
	op.drop_column('request', sa.Column('profile_image', sa.Text))
	op.drop_column('request', sa.Column('user_first_name', sa.Text))
	op.drop_column('request', sa.Column('user_last_name', sa.Text))
    
