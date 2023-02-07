import functools
import hashlib
from typing import Optional, List

from flask import jsonify
from flask_restful import reqparse
from loguru import logger

from src import cache, app, db
from src.core.database.models import User, Backup
from src.utils import RSACipher, ResponseCode


@cache.memoize(timeout=100, hash_method=hashlib.sha256)
def find_user_by_id(user_id: int) -> Optional[User]:
    with app.app_context():
        return User.query.filter(User.user_id == user_id).first()


@cache.memoize(timeout=30, hash_method=hashlib.sha256)
def find_backup_by_id(backup_id: int, user_id: int) -> Optional[Backup]:
    with app.app_context():
        return Backup.query\
            .filter_by(backup_id=backup_id, user_id=user_id)\
            .join(User)\
            .add_columns(Backup.backup_id, Backup.user_id, Backup.created, Backup.comment, User.login)\
            .first()


def delete_backup(backup_id: int) -> int:
    with app.app_context():
        ret = Backup.query.filter_by(backup_id=backup_id).delete()
        db.session.commit()
        return ret


@cache.memoize(timeout=30, hash_method=hashlib.sha256)
def find_user_backups_by_id(user_id: int) -> List[Backup]:
    with app.app_context():
        return User.query\
            .filter(User.user_id == user_id)\
            .join(Backup, Backup.user_id == User.user_id, isouter=True)\
            .add_columns(User.user_id, User.login, User.joined, Backup.backup_id, Backup.created, Backup.comment)\
            .limit(10)\
            .all()


@cache.memoize(timeout=30, hash_method=hashlib.sha256)
def find_user_by_login(username: str) -> Optional[User]:
    with app.app_context():
        return User.query.filter(User.login == username).first()


def auth_required(f):

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers", required=True, help="Missing auth token!")
        parsed_args = parser.parse_args()
        token = parsed_args["Authorization"]
        decoded = RSACipher.provide().jwt_decode(token)
        user_id = decoded.get("user_id", None) if decoded else None
        if not decoded or not user_id:
            ret = jsonify({
                "message": "Invalid auth token!"
            })
            ret.status_code = ResponseCode.UNAUTHORIZED.value
            return ret
        else:
            return f(*args, **kwargs)
    return wrapper