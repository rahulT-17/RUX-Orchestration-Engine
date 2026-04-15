from __future__ import annotations

import os
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from database import AsyncSessionLocal


def get_expected_revision() -> str:
    # Alembic head = latest migration revision available in the codebase.
    project_root = Path(__file__).resolve().parent.parent
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    script = ScriptDirectory.from_config(alembic_cfg)
    head = script.get_current_head()
    if head is None:
        raise RuntimeError("No Alembic head revision found.")
    return head


async def ensure_schema_revision() -> None:
    # Keep this guard switchable so local bootstrap can run before first stamp.
    if os.getenv("ENABLE_SCHEMA_REVISION_GUARD", "false").lower() != "true":
        return

    expected = get_expected_revision()

    async with AsyncSessionLocal() as session:
        # alembic_version stores the revision currently applied in this database.
        result = await session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        current = result.scalar_one_or_none()

    if current is None:
        raise RuntimeError("Database is not stamped. Run: alembic stamp head")

    if current != expected:
        raise RuntimeError(
            f"Database revision {current} does not match app revision {expected}. "
            "Run: alembic upgrade head"
        )