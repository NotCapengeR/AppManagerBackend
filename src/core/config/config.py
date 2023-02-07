import os
from typing import Final

from src.core.database.common import SQLITE_URI, MIGRATION_DIR, CACHE_DIRECTORY, ALEMBIC_SCRIPT_ENV, DOWNLOAD_PATH


class Config(object):
    PORT: Final[int] = 9999
    HOST: Final[str] = "127.0.0.1"
    TESTING: Final[bool] = True
    SQLALCHEMY_ECHO: Final[bool] = True
    SQLALCHEMY_DATABASE_URI: Final[str] = SQLITE_URI
    SQLALCHEMY_MIGRATE_REPO: Final[str] = MIGRATION_DIR
    USER_BACKUPS_PATH: Final[str] = DOWNLOAD_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS: Final[bool] = False
    CACHE_TYPE: Final[str] = "FileSystemCache"
    CACHE_DIR: Final[str] = CACHE_DIRECTORY
    CACHE_DEFAULT_TIMEOUT: Final[int] = 300_000
    CACHE_THRESHOLD: Final[int] = 30_000
    ALEMBIC: Final[dict] = {
        "script_location": ALEMBIC_SCRIPT_ENV,
        "file_template": "%%(day).2d.%%(month).2d.%%(year).d_%%(hour).2d.%%(minute).2d.%%(second).2d_%%(rev)s_%%(slug)s"
    }
    SECRET_KEY: Final[str] = \
        "/lALJKALJKHK3dsadas2312!!!312132>!Js(71-'dJ!hadsdasdasgjh12gh+fz11ajkhkfsajhkhjdsKAasdasdasGA;kdf;sladj;lkskd;l312j312lk312312"

    def __init__(self):
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)
        if not os.path.exists(self.USER_BACKUPS_PATH):
            os.makedirs(self.USER_BACKUPS_PATH)
