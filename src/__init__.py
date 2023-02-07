from flask import Flask
from flask_alembic import Alembic
from flask_caching import Cache
from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

from src.core.config import Config

app: Flask = Flask(__name__)
config = Config()
app.config.from_object(config)
cache: Cache = Cache(app)
db: SQLAlchemy = SQLAlchemy(app=app)
migrate: Migrate = Migrate(app, db, directory=config.SQLALCHEMY_MIGRATE_REPO)
alembic: Alembic = Alembic(app)
api: Api = Api(app, prefix="/api")
