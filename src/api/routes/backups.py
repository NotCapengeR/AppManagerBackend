import base64
import os
from pathlib import Path

from flask import Response, jsonify, current_app, send_file, request
from flask_restful import Resource, reqparse
from loguru import logger
from requests_toolbelt import MultipartEncoder
from werkzeug.datastructures import FileStorage

from src import db, cache, app
from src.api.routes.common import find_user_by_id, find_user_backups_by_id, find_backup_by_id, delete_backup
from src.core.database.models import Backup, BACKUP_PER_PAGE
from src.utils import ResponseCode, RSACipher, ContentType, Encodings


class DownloadBackup(Resource):
    url = "/backups/<int:backup_id>/download"

    def get(self, backup_id: int) -> Response:
        logger.info(request.headers)
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers", required=True, help="Missing auth token!")
        args = parser.parse_args()
        token = args["Authorization"]
        decoded = RSACipher.provide().jwt_decode(token)
        user_id = decoded.get("user_id", None) if decoded else None
        if not decoded or not user_id:
            ret = jsonify({
                "message": "Invalid auth token!"
            })
            ret.status_code = ResponseCode.UNAUTHORIZED.value
            return ret
        backup = find_backup_by_id(backup_id, user_id)
        if not backup:
            ret = jsonify({
                "message": "Backups is not found!"
            })
            ret.status_code = ResponseCode.NOT_FOUND.value
            return ret
        download_path = os.path.join(
            current_app.config["USER_BACKUPS_PATH"],
            f"{backup.backup_id}-{backup.user_id} [{backup.created.strftime('%d-%m-%Y_%H;%M;%S.%f')}].zip"
        )
        resp = send_file(download_path)
     #   resp.headers["Connection"] = "close"
        logger.debug(resp.headers)
        return resp


class BackupManager(Resource):
    url = "/backups/<int:backup_id>"

    def get(self, backup_id: int) -> Response:
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers", required=True, help="Missing auth token!")
        args = parser.parse_args()
        token = args["Authorization"]
        decoded = RSACipher.provide().jwt_decode(token)
        user_id = decoded.get("user_id", None) if decoded else None
        if not decoded or not user_id:
            ret = jsonify({
                "message": "Invalid auth token!"
            })
            ret.status_code = ResponseCode.UNAUTHORIZED.value
            return ret
        backup = find_backup_by_id(backup_id, user_id)
        if not backup:
            ret = jsonify({
                "message": "Backups is not found!"
            })
            ret.status_code = ResponseCode.NOT_FOUND.value
            return ret
        return jsonify({
            "backup_id": backup.backup_id,
            "user_id": backup.user_id,
            "username": backup.login,
            "comment": backup.comment,
            "created": str(backup.created),
        })

    def delete(self, backup_id: int) -> Response:
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers", required=True, help="Missing auth token!")
        args = parser.parse_args()
        token = args["Authorization"]
        decoded = RSACipher.provide().jwt_decode(token)
        user_id = decoded.get("user_id", None) if decoded else None
        if not decoded or not user_id:
            ret = jsonify({
                "message": "Invalid auth token!"
            })
            ret.status_code = ResponseCode.UNAUTHORIZED.value
            return ret
        backup = find_backup_by_id(backup_id, user_id)
        if not backup:
            ret = jsonify({
                "message": "Backups is not found!"
            })
            ret.status_code = ResponseCode.NOT_FOUND.value
            return ret
        download_path = Path(os.path.join(
            current_app.config["USER_BACKUPS_PATH"],
            f"{backup.backup_id}-{backup.user_id} [{backup.created.strftime('%d-%m-%Y_%H;%M;%S.%f')}].zip")
        )
        delete_backup(backup.backup_id)
        if download_path.exists():
            download_path.unlink()
        cache.delete_memoized(find_backup_by_id)
        return jsonify({"message": f"Backup with id {backup_id} was successfully deleted!"})


class BackupProvider(Resource):
    url = "/backups"

    def get(self) -> Response:
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers", required=True, help="Missing auth token!")
        args = parser.parse_args()
        token = args["Authorization"]
        decoded = RSACipher.provide().jwt_decode(token)
        user_id = decoded.get("user_id", None) if decoded else None
        if not decoded or not user_id:
            ret = jsonify({
                "message": "Invalid auth token!"
            })
            ret.status_code = ResponseCode.UNAUTHORIZED.value
            return ret
        backups = find_user_backups_by_id(user_id)
        if not backups:
            ret = jsonify({
                "message": "User/backups is/are not found!"
            })
            ret.status_code = ResponseCode.NOT_FOUND.value
            return ret
        serialized = [
            {
                "backup_id": backup.backup_id,
                "user_id": backup.user_id,
                "username": backup.login,
                "comment": backup.comment,
                "created": str(backup.created),
            } for backup in backups
        ]
        return jsonify(serialized)

    def post(self) -> Response:
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers", required=True, help="Missing auth token!")
        parser.add_argument("comment", location="form")
        parser.add_argument("file", location="files", type=FileStorage, required=True, help="Missing backup .zip file!")
        args = parser.parse_args()
        token = args["Authorization"]
        decoded = RSACipher.provide().jwt_decode(token)
        user_id = decoded.get("user_id", None) if decoded else None
        if not decoded or not user_id:
            ret = jsonify({
                "message": "Invalid auth token!"
            })
            ret.status_code = ResponseCode.UNAUTHORIZED.value
            return ret
        user_with_backups = find_user_backups_by_id(user_id)
        if not user_with_backups:
            ret = jsonify({
                "message": "Invalid auth token!"
            })
            ret.status_code = ResponseCode.UNAUTHORIZED.value
            return ret
        if len(user_with_backups) >= 10:
            ret = jsonify({
                "message": "Backups limit reached!"
            })
            ret.status_code = ResponseCode.CONFLICT.value
            return ret
        comment = args.get("comment", None)
        backup = Backup.create(user_id, comment)
        with app.app_context():
            db.session.add(backup)
            db.session.flush()
            ret = {
                "backup_id": backup.backup_id,
                "user_id": backup.user_id,
                "username": user_with_backups[0].login,
                "comment": backup.comment,
                "created": str(backup.created),
            }
            file = args["file"]
            file.save(os.path.join(current_app.config["USER_BACKUPS_PATH"], backup.download_path))
            db.session.commit()
        return jsonify(ret)
