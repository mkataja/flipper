"""add user emoji_enabled

Revision ID: 75e45dc42a20
Revises: 
Create Date: 2026-03-12 15:23:44.039988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75e45dc42a20'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("user"):
        return

    columns = {column["name"] for column in inspector.get_columns("user")}
    if "emoji_enabled" not in columns:
        op.add_column(
            "user",
            sa.Column(
                "emoji_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("user"):
        return

    columns = {column["name"] for column in inspector.get_columns("user")}
    if "emoji_enabled" in columns:
        op.drop_column("user", "emoji_enabled")
