#!/flask/bin/python
# -*- coding: UTF-8 -*-
from typing import NoReturn

from src import app, api, config, db
from src.core.database.models import User, Backup
from src.api.routes import Login, Register, BackupManager, BackupProvider, DownloadBackup


def main() -> NoReturn:
    with app.app_context():
        db.create_all()
    api.add_resource(Login, Login.url)
    api.add_resource(Register, Register.url)
    api.add_resource(BackupManager, BackupManager.url)
    api.add_resource(BackupProvider, BackupProvider.url)
    api.add_resource(DownloadBackup, DownloadBackup.url)
    app.run(host=config.HOST, port=config.PORT, debug=config.TESTING)


if __name__ == "__main__":
    main()
