"""empty message

Revision ID: 6434c09f4284
Revises: b9e6e7d9e4b3
Create Date: 2022-06-02 17:35:34.995179

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6434c09f4284'
down_revision = 'b9e6e7d9e4b3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_comments_timestamp'), ['timestamp'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_comments_timestamp'))

    # ### end Alembic commands ###
