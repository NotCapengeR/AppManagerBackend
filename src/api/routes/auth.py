from flask import Response, jsonify
from flask_restful import Resource, reqparse

from src import app, db
from src.api.routes.common import find_user_by_id, find_user_by_login
from src.core.database.models import User, verify_password
from src.utils import RSACipher, ResponseCode


class Login(Resource):
    url = "/users/login"

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
        user = find_user_by_id(user_id)
        if not user:
            ret = jsonify({
                "message": "User is not found!"
            })
            ret.status_code = ResponseCode.NOT_FOUND.value
            return ret
        return jsonify(user.serialize())

    def post(self) -> Response:
        parser = reqparse.RequestParser()
        parser.add_argument("username", location="form", required=True, help="'Username' is a required field!")
        parser.add_argument("password", location="form", required=True, help="'Password' is a required field!")
        args = parser.parse_args()
        username = args["username"]
        user = find_user_by_login(username)
        if not user:
            ret = jsonify({
                "message": "Invalid Credentials!"
            })
            ret.status_code = ResponseCode.UNAUTHORIZED.value
            return ret
        if not verify_password(args["password"], user.password_hash):
            ret = jsonify({
                "message": "Invalid Credentials!"
            })
            ret.status_code = ResponseCode.UNAUTHORIZED.value
            return ret
        return jsonify(user.serialize() | {"token": user.token})


class Register(Resource):
    url = "/users/register"

    def post(self) -> Response:
        parser = reqparse.RequestParser()
        parser.add_argument("username", location="form", required=True, help="'Username' is a required field!")
        parser.add_argument("password", location="form", required=True, help="'Password' is a required field!")
        args = parser.parse_args()
        username = args["username"]
        user = find_user_by_login(username)
        if user:
            ret = jsonify({
                "message": "This user is already exists!"
            })
            ret.status_code = ResponseCode.CONFLICT.value
            return ret
        user = User.create_user(username, args["password"])
        with app.app_context():
            db.session.add(user)
            db.session.flush()
            ret = user.serialize() | {"token": user.token}
            db.session.commit()
        return jsonify(ret)
