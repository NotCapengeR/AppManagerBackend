import base64
import datetime
import enum
import os
import string
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Final, Union, Optional, Dict, Any

from Crypto.Hash import (
    SHA512, SHA256, MD5, MD2, SHA1, SHA224, SHA384, SHA3_224, SHA3_256, SHA3_512, SHA3_384, HMAC
)
from Crypto.Protocol.KDF import PBKDF2
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Random import get_random_bytes
from jwt import JWT, jwk_from_pem
from loguru import logger
from strenum import StrEnum

from src.utils.date_utils import int_timestamp, with_delta

EMPTY_STRING: Final[str] = string.whitespace[0]
STORAGE_PATH: Final[str] = os.path.join(Path(os.path.dirname(__file__)).parent, "core\\store")


class HashAlg(Enum):
    SHA1 = SHA1
    SHA224 = SHA224
    SHA256 = SHA256
    SHA384 = SHA384
    SHA512 = SHA512
    SHA3_224 = SHA3_224
    SHA3_256 = SHA3_256
    SHA3_384 = SHA3_384
    SHA3_512 = SHA3_512
    MD2 = MD2
    MD5 = MD5

    def hash(self, data: Union[str, bytes]):
        if not isinstance(data, bytes):
            data = data.encode(Encodings.UTF_8)
        return self.value.new(data)


@enum.unique
class Encodings(StrEnum):
    UTF_8 = "utf-8"
    UTF_16 = "utf-16"
    WINDOWS_1251 = "windows 1251"
    CHCP_65001 = "chcp 65001"
    CP_1251 = "cp1251"
    CP_866 = "cp866"
    ASCII = "ascii"
    US_ASCII = "us-ascii"
    ISO_8859_1 = "iso-8859-1"
    BIG5 = "big5"
    BIG5_HKSCS = "big5-hkscs"
    CESU_8 = "cesu-8"


@enum.unique
class PaddingStyle(StrEnum):
    PCKS7 = "pkcs7"
    X923 = "x923"
    ISO7816 = "iso7816"


class HashVerifier(object):
    KEYS_PATH: Final[str] = os.path.join(STORAGE_PATH, "key_for_hash.pem")
    PASSPHRASE: Final[str] = base64.b64encode(SHA512.new(b"Top secret").digest()).decode(Encodings.UTF_8)
    PREFIX: Final[bytes] = b"aQsXqDlSKxhJaMNhjIkF:"
    PREFIX_LEN: Final[int] = len(PREFIX)
    PBKDF2_ITERATIONS: Final[int] = 20_000
    KEY_SIZE_MODE_256: Final[int] = 32
    SALT_SIZE: Final[int] = 32
    instance: Optional["HashVerifier"] = None

    def __init__(self):
        self._key = self._get_key()

    @property
    def key(self) -> bytes:
        return self._key

    def _calculate_key(self, salt: bytes) -> bytes:
        return PBKDF2(
            self.key.decode(Encodings.UTF_8),
            salt,
            self.KEY_SIZE_MODE_256,
            count=self.PBKDF2_ITERATIONS,
            hmac_hash_module=SHA512
        )

    @classmethod
    def generate_key(cls) -> bytes:
        key = RSA.generate(3072)
        encrypted_key = key.export_key(passphrase=cls.PASSPHRASE, pkcs=8, protection="scryptAndAES256-CBC")
        file = open(cls.KEYS_PATH, "wb")
        file.write(encrypted_key)
        file.close()
        return encrypted_key

    def generate_hash(self, data: Union[str, bytes], alg: HashAlg) -> bytes:
        if not isinstance(data, bytes):
            data = data.encode(Encodings.UTF_8)
        salt: bytes = get_random_bytes(self.SALT_SIZE)
        key = self._calculate_key(salt)
        hmac = HMAC.new(key, digestmod=alg.value, msg=data + salt)
        password_hash = hmac.digest()
        return self.PREFIX + base64.b64encode(password_hash + salt)

    def verify_data(self, data: Union[str, bytes], data_hash: Union[str, bytes], alg: HashAlg) -> bool:
        if not isinstance(data, bytes):
            data = data.encode(Encodings.UTF_8)
        if not isinstance(data_hash, bytes):
            data_hash = data_hash.encode(Encodings.UTF_8)
        msg = base64.b64decode(data_hash[self.PREFIX_LEN:])
        salt = msg[-self.SALT_SIZE:]
        msg = msg[:-self.SALT_SIZE]
        key = self._calculate_key(salt)
        hmac = HMAC.new(key, digestmod=alg.value, msg=data + salt)
        try:
            hmac.verify(msg)
            return True
        except ValueError:
            return False

    @classmethod
    def _get_key(cls) -> bytes:
        with open(cls.KEYS_PATH, "rb") as file:
            encoded_key = file.read()
            key: RsaKey = RSA.import_key(encoded_key, passphrase=cls.PASSPHRASE)
            file.flush()
        return key.export_key().replace(b"-----BEGIN RSA PRIVATE KEY-----\n", b"") \
                   .replace(b"\n-----END RSA PRIVATE KEY-----", b"") + key.publickey().export_key() \
                   .replace(b"-----BEGIN PUBLIC KEY-----\n", b"") \
                   .replace(b"\n-----END PUBLIC KEY-----", b"")

    @classmethod
    def provide(cls) -> "HashVerifier":
        if not cls.instance:
            cls.instance = HashVerifier()
        return cls.instance


class RSACipher(object):
    """Class for implementation RSA+PKCS1_OAEP encryption"""
    KEYS_PATH: Final[str] = os.path.join(STORAGE_PATH, "jwt.pem")
    PASSPHRASE: Final[str] = base64.b64encode(SHA512.new(b"ABCDADCAKA").digest()).decode(Encodings.UTF_8)
    PREFIX: Final[bytes] = b"uiJaX0jDSqWrtIPfSxK:"
    PREFIX_LEN: Final[int] = len(PREFIX)
    SALT_SIZE: Final[int] = 32
    instance: Optional["RSACipher"] = None
    AUTH_PREFIX: Final[str] = "JWT "

    def __init__(self) -> None:
        self.key = self._get_key()
        self.jwt = JWT()
        self.jwt_signing_public = jwk_from_pem(self.public_key.export_key())
        self.jwt_signing_private = jwk_from_pem(self.key.export_key())

    def jwt_encode(self, payload: Dict[str, Any]) -> str:
        if "exp" not in payload:
            payload["exp"] = int_timestamp(with_delta(weeks=30))
        if "iat" not in payload:
            payload["iat"] = int_timestamp(datetime.datetime.utcnow())
        _id = uuid.uuid4().hex
        if "jti" not in payload:
            payload["jti"] = uuid.uuid4().hex

        return self.AUTH_PREFIX + self.jwt.encode(
            payload,
            self.jwt_signing_private,
            alg="RS512",
            optional_headers={"kid": _id}
        )

    def jwt_decode(self, token: str) -> Optional[Dict[str, Any]]:
        if not token.startswith(self.AUTH_PREFIX):
            return None
        try:
            return self.jwt.decode(token[len(self.AUTH_PREFIX):], self.jwt_signing_public)
        except BaseException as error:
            logger.error(f"{type(error).__name__}: {str(error)}")
            return None

    @property
    def public_key(self) -> RsaKey:
        return self.key.public_key()

    @classmethod
    def provide(cls) -> "RSACipher":
        if not cls.instance:
            cls.instance = RSACipher()
        return cls.instance

    @classmethod
    def _get_key(cls) -> RsaKey:
        with open(cls.KEYS_PATH, "rb") as file:
            encoded_key = file.read()
            key: RsaKey = RSA.import_key(encoded_key, passphrase=cls.PASSPHRASE)
            file.flush()
        return key

    @classmethod
    def generate_key(cls) -> bytes:
        key = RSA.generate(3072)
        encrypted_key = key.export_key(passphrase=cls.PASSPHRASE, pkcs=8, protection="scryptAndAES256-CBC")
        file = open(cls.KEYS_PATH, "wb")
        file.write(encrypted_key)
        file.close()
        return encrypted_key
