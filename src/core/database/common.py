import os
from typing import Final

DATABASE_DIR: Final[str] = os.path.dirname(__file__)
CACHE_DIRECTORY: Final[str] = os.path.join(DATABASE_DIR, "cache")
DOWNLOAD_PATH: Final[str] = os.path.join(DATABASE_DIR, "downloads")
DATABASE_PATH: Final[str] = os.path.join(DATABASE_DIR, "app.sqlite")
MIGRATION_DIR: Final[str] = os.path.join(DATABASE_DIR, "repository")
ALEMBIC_SCRIPT_ENV: Final[str] = os.path.join(DATABASE_DIR, "migrations")
ALEMBIC_VERSION_PATH: Final[str] = os.path.join(ALEMBIC_SCRIPT_ENV, "versions")
SQLITE_URI: Final[str] = f"sqlite:///{DATABASE_PATH}"
