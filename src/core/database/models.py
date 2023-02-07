import hashlib
from datetime import datetime
from typing import Final, Dict, Optional

from loguru import logger

from src import db, cache, app
from src.utils import HashVerifier, HashAlg, RSACipher

LOGIN_MAX_SIZE: Final[int] = 30
BACKUP_PER_PAGE: Final[int] = 20


def hash_from_password(password: str | bytes) -> bytes:
    return HashVerifier.provide().generate_hash(password, HashAlg.SHA512)


@cache.memoize(hash_method=hashlib.sha256)
def verify_password(input_password: str | bytes, password_hash: str | bytes) -> bool:
    return HashVerifier.provide().verify_data(input_password, password_hash, HashAlg.SHA512)


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True, index=True)
    login = db.Column(db.String(LOGIN_MAX_SIZE), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.LargeBinary, nullable=False)
    joined = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def serialize(self) -> Dict[str, Dict[str, str | int]]:
        return {
            "user": {
                "user_id": self.user_id,
                "username": self.login,
                "joined": str(self.joined),
            }
        }

    @property
    def token(self) -> str:
        return RSACipher.provide().jwt_encode({"user_id": self.user_id})

    @staticmethod
    def create_user(username: str, password: str) -> "User":
        return User(
            login=username,
            joined=datetime.utcnow(),
            password_hash=hash_from_password(password)
        )


class Backup(db.Model):
    __tablename__ = "backups"
    backup_id = db.Column(db.Integer, primary_key=True, index=True)
    user = db.relationship("User", backref=db.backref("builds", lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    comment = db.Column(db.Text)

    def format_time_for_path(self) -> str:
        return self.created.strftime("%d-%m-%Y_%H;%M;%S.%f")

    @property
    def download_path(self) -> str:
        return f"{self.backup_id}-{self.user_id} [{self.format_time_for_path()}].zip"

    @staticmethod
    def create(user_id: int, comment: Optional[str] = None) -> "Backup":
        return Backup(
            user_id=user_id,
            created=datetime.utcnow(),
            comment=comment
        )


@logger.catch()
def main() -> None:
    with app.app_context():
        Backup.query.delete()
        db.session.commit()


if __name__ == "__main__":
    main()
