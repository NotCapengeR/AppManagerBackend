#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys
from pathlib import Path
from typing import Final

from loguru import logger
from migrate.versioning import api

from src import db, app


from src.core.database.models import Backup, User

from src.core.database.common import MIGRATION_DIR, SQLITE_URI

LOG_PATH: Final[str] = os.path.join(Path(os.path.dirname(__file__)).parent, "logs\\debug.log")


@logger.catch()
def main() -> None:
    logger.level("TRACE", color="<e>")
    logger.level("DEBUG", color="<m>")
    logger.level("WARNING", color="<fg #d8f007>")
    logger.configure(handlers=[{
        "sink": sys.stderr,
        "level": "TRACE",
        "format":
            "<fg #10fd02>{time:DD-MM-YYYY, HH:MM:ss.SSSSSS}</fg #10fd02> — <level>{message} [{name}:{function}:{line}]</level> | <level>{level}</level>",
        "enqueue": True,
        "colorize": True,
        "diagnose": True,
    }])
    handler_id: int = logger.add(
        LOG_PATH,
        level="TRACE",
        format="{time:DD-MM-YYYY, HH:MM:ss.SSSSSS} — {message} [{name}:{function}:{line}] | {level}",
        enqueue=True,
        diagnose=True,
    )
    with app.app_context():
        db.create_all()

        if not os.path.exists(MIGRATION_DIR):
            api.create(MIGRATION_DIR, "repository")
            api.version_control(SQLITE_URI, MIGRATION_DIR)
        else:
            api.version_control(SQLITE_URI, MIGRATION_DIR, api.version(MIGRATION_DIR))
        logger.success(f"Database {SQLITE_URI} was created successful!")
    logger.remove(handler_id)


if __name__ == "__main__":
    main()