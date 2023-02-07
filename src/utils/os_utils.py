import enum
import hashlib
import math
import os
from os import PathLike
from pathlib import Path
from typing import Final, Union


BYTES_IN_KB: Final[int] = 1024
BYTES_IN_MB: Final[int] = int(math.pow(BYTES_IN_KB, 2))
BYTES_IN_GB: Final[int] = int(math.pow(BYTES_IN_KB, 3))


@enum.unique
class ChecksumHash(enum.Enum):
    MD5 = hashlib.md5
    SHA_1 = hashlib.sha1
    SHA_224 = hashlib.sha224
    SHA_256 = hashlib.sha256
    SHA_384 = hashlib.sha384
    SHA_512 = hashlib.sha512


M_PATH = Union[Path, str, bytes, PathLike[str], PathLike[bytes], int]


def file_checksum(path: M_PATH, hash_alg: ChecksumHash) -> str:
    if not isinstance(hash_alg, ChecksumHash):
        raise TypeError(f"Error: parameter 'hash' must be a {type(ChecksumHash)}! Given type: {type(hash_alg)}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Error: file '{path}' is not found!")
    with open(path, "rb") as file:
        file_hash = hash_alg.value()
        while chunk := file.read(BYTES_IN_KB * 8):
            file_hash.update(chunk)
    return file_hash.hexdigest()
