import asyncio
import enum
import socket
from dataclasses import dataclass
from enum import IntEnum
from typing import (
    TypeVar, Generic, Optional, Tuple, Any, Union
)

from aiohttp import RequestInfo, ClientSession, ClientResponse
from aiohttp.client_reqrep import ContentDisposition
from aiohttp.connector import Connection, TCPConnector
from aiohttp.typedefs import RawHeaders
from aiohttp.web_exceptions import HTTPException
from loguru import logger
from multidict import CIMultiDictProxy, MultiDictProxy
from strenum import StrEnum
from yarl import URL


@enum.unique
class ResMethod(StrEnum):
    TEXT = enum.auto()
    JSON = enum.auto()


@enum.unique
class ContentType(StrEnum):
    APPLICATION_JSON = "application/json"
    APPLICATION_JSON_LD = "application/ld+json"
    APPLICATION_XML = "application/xml"
    APPLICATION_JAVASCRIPT = "application/javascript"
    APPLICATION_FORM_URL_ENCODED = "application/x-www-form-urlencoded"
    APPLICATION_OCTET_STREAM = "application/octet-stream"
    APPLICATION_ZIP = "application/zip"
    APPLICATION_7Z = "application/x-7z-compressed"
    APPLICATION_X_RAR = "application/x-rar"
    APPLICATION_RAR = "application/vnd.rar"
    APPLICATION_JAVA_ARCHIVE = "application/java-archive"
    APPLICATION_PHP = "application/x-httpd-php"
    APPLICATION_SQLITE3 = "application/x-sqlite3"
    APPLICATION_PDF = "application/pdf"
    APPLICATION_OGG = "application/ogg"
    APPLICATION_APPLE_PACKAGE_INSTALLER = "application/vnd.apple.installer+xml"
    APPLICATION_OPEN_DOCUMENT_PRESENTATION = "application/vnd.oasis.opendocument.presentation"
    APPLICATION_OPEN_DOCUMENT_SPREADSHEET = "application/vnd.oasis.opendocument.spreadsheet"
    APPLICATION_OPEN_DOCUMENT_TEXT = "application/vnd.oasis.opendocument.text"
    APPLICATION_XHTML = "application/xhtml+xml"
    APPLICATION_XLS = "application/vnd.ms-excel"
    APPLICATION_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    APPLICATION_VISIO = "application/vnd.visio"
    APPLICATION_TAR = "application/x-tar"
    APPLICATION_PPT = "application/vnd.ms-powerpoint"
    APPLICATION_RICH_TEXT = "application/rtf"
    APPLICATION_PDB = "application/x-ms-pdb"
    APPLICATION_ARCHIVE = "application/x-archive"
    APPLICATION_SHELL = "application/x-sh"
    APPLICATION_PE = "application/vnd.microsoft.portable-executable"
    APPLICATION_EXE = "application/x-dosexec"
    APPLICATION_APK = "application/vnd.android.package-archive"
    APPLICATION_PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    AUO_OGG = "audio/ogg"
    AUDIO_WAW = "audio/wav"
    AUDIO_MIDI = "audio/x-midi"
    AUDIO_WEBM = "audio/webm"
    AUDIO_MPEG = "audio/mpeg"
    AUDIO_WEBP = "audio/webp"
    AUDIO_OPUS = "audio/opus"

    VIDEO_OGG = "video/ogg"

    TEXT_PLAIN = "text/plain"
    TEXT_XML = "text/xml"
    TEXT_PYTHON = "text/x-python"
    TEXT_BATCH = "text/x-msdos-batch"
    TEXT_C_PLUS_PLUS = "text/x-c"
    TEXT_HTML = "text/html"
    TEXT_CSS = "text/css"

    IMAGE_APNG = "image/apng"
    IMAGE_AVIF = "image/avif"
    IMAGE_BMP = "image/bmp"
    IMAGE_ICO = "image/vnd.microsoft.icon"
    IMAGE_TIFF = "image/tiff"
    IMAGE_GIF = "image/gif"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_SVG = "image/svg+xml"
    IMAGE_PNG = "image/png"

    FONT_OTF = "font/otf"
    FONT_TTF = "font/ttf"
    FONT_WOFF = "font/woff"
    FONT_WOFF2 = "font/woff2"

    MULTIPART_FORM_DATA = "multipart/form-data"
    ALL = "*/*"


@enum.unique
class RequestMethod(StrEnum):
    GET = enum.auto()
    POST = enum.auto()
    DELETE = enum.auto()
    PUT = enum.auto()
    PATCH = enum.auto()
    HEAD = enum.auto()
    COPY = enum.auto()
    OPTIONS = enum.auto()
    LINK = enum.auto()
    UNLINK = enum.auto()
    PURGE = enum.auto()
    LOCK = enum.auto()
    UNLOCK = enum.auto()
    PROPFIND = enum.auto()
    VIEW = enum.auto()


class ResponseCode(IntEnum):
    CONTINUE = 100
    SWITCHING_PROTOCOL = 101
    PROCESSING = 102
    EARLY_HINTS = 103

    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NON_AUTHORITATIVE_INFORMATION = 203
    NO_CONTENT = 204
    RESET_CONTENT = 205
    PARTIAL_CONTENT = 206
    MULTI_STATUS = 207
    ALREADY_REPORTED = 208
    IM_USED = 226

    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    USE_PROXY = 305
    SWITCHING_PROXY = 306
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    PROXY_AUTHENTICATION_REQUIRED = 407
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    LENGTH_REQUIRED = 411
    PRECONDITION_FAILED = 412
    PAYLOAD_TOO_LARGE = 413
    URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    RANGE_NOT_SATISFIABLE = 416
    EXPECTATION_FAILED = 417
    IM_A_TEAPOT = 418  # CRINGE
    PAGE_EXPIRED = 419
    METHOD_FAILURE = 420
    ENHANCE_YOUR_CALM = 420  # TWITTER
    LOGIN_TIMEOUT = 420
    MISDIRECTED_REQUEST = 421
    UNPROCESSABLE_ENTITY = 422
    LOCKED = 423
    FAILED_DEPENDENCY = 424
    TOO_EARLY = 425
    UPGRADE_REQUIRED = 426
    PRECONDITION_REQUIRED = 428
    TOO_MANY_REQUESTS = 429
    REQUEST_HEADER_FIELDS_TOO_LARGE_SHOPIFY = 430
    REQUEST_HEADER_FIELDS_TOO_LARGE = 431
    NO_RESPONSE = 444
    RETRY_WITH = 449
    UNAVAILABLE_FOR_LEGAL_REASONS = 451
    REDIRECT = 451
    REQUEST_HEADER_TOO_LARGE = 494
    SSL_CERTIFICATE_ERROR = 495
    SSL_CERTIFICATE_REQUIRED = 496
    HTTP_REQUEST_SENT_TO_HTTPS_PORT = 497
    INVALID_TOKEN = 498
    TOKEN_REQUIRED = 499
    CLIENT_CLOSED_REQUEST = 499

    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    TIMEOUT_GATEWAY = 504
    HTTP_VERSION_NOT_SUPPORTED = 505
    VARIANT_ALSO_NEGOTIATES = 506
    INSUFFICIENT_STORAGE = 507
    LOOP_DETECTED = 508
    BANDWIDTH_LIMIT_EXCEEDED = 509
    NOT_EXTENDED = 510
    NETWORK_AUTHENTICATION_REQUIRED = 511
    WEB_SERVER_RETURNED_AN_UNKNOWN_ERROR = 520
    WEB_SERVER_IS_DOWN = 521
    CONNECTION_TIMED_OUT = 522
    ORIGIN_IS_UNREACHABLE = 523
    A_TIMEOUT_OCCURRED = 524
    INVALID_SSL_CERTIFICATE = 526
    RAILGUN_ERROR = 527
    SITE_IS_OVERLOADED = 529
    SITE_IS_FROZEN = 530
    CLOUDFLARE_INFORMATION = 530
    NETWORK_READ_TIMEOUT_ERROR = 598
    NETWORK_CONNECT_TIMEOUT_ERROR = 599

    # Custom codes
    NO_ERROR = 0
    ERROR_OCCURRED_CODE = -1


T = TypeVar("T")


@dataclass()
class NetworkResultAsync(Generic[T]):

    def __init__(
            self,
            data: T,
            code: int,
            response: Optional[ClientResponse] = None,
            error: Optional[BaseException] = None
    ) -> None:
        self.data = data
        self.code = code
        self.response = response
        self.error = error

    def __str__(self) -> str:
        return f"<NetworkResult(data={self.data}, code={self.code}, response={self.response}, error={self.error})>"

    def __repr__(self):
        return str(self)

    def is_success(self) -> bool:
        return self.error is None and 200 <= self.code < 400

    @property
    def raw_headers(self) -> RawHeaders:
        return self.response.raw_headers

    @property
    def headers(self) -> "CIMultiDictProxy[str]":
        return self.response.headers

    @property
    def request_info(self) -> RequestInfo:
        return self.response.request_info

    @property
    def content_disposition(self) -> Optional[ContentDisposition]:
        return self.response.content_disposition

    @property
    def host(self) -> str:
        return self.response.host

    @property
    def url(self) -> URL:
        return self.response.url

    @property
    def real_url(self) -> URL:
        return self.response.real_url

    @property
    def connection(self) -> Optional["Connection"]:
        return self.response.connection

    @property
    def history(self) -> Tuple["ClientResponse", ...]:
        return self.response.history

    @property
    def links(self) -> "MultiDictProxy[MultiDictProxy[Union[str, URL]]]":
        return self.response.links

    @property
    def closed(self) -> bool:
        return self.response.closed

    @property
    def ok(self) -> bool:
        return self.response.ok


class HTTPSession(ClientSession):
    """ Abstract class for aiohttp. """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def __del__(self, **kwargs) -> None:
        """
        Closes the ClientSession instance
        cleanly when the instance is deleted.
        Useful for things like when the interpreter closes.
        This would be perfect if discord.py had this as well. :thinking:
        :param **kwargs:
        """
        super(HTTPSession, self).__del__()
        if not self.closed:
            asyncio.run(self.close())

    async def get_result(self, url, *args, **kwargs) -> NetworkResultAsync[Any]:
        return await self.query(url, RequestMethod.GET, *args, **kwargs)

    async def post_result(self, url, *args, **kwargs) -> NetworkResultAsync[Any]:
        return await self.query(url, RequestMethod.POST, *args, **kwargs)

    async def head_result(self, url, *args, **kwargs) -> NetworkResultAsync[Any]:
        return await self.query(url, RequestMethod.HEAD, *args, **kwargs)

    async def options_result(self, url, *args, **kwargs) -> NetworkResultAsync[Any]:
        return await self.query(url, RequestMethod.OPTIONS, *args, **kwargs)

    async def query(self, url, method: RequestMethod = RequestMethod.GET, res_method=ResMethod.TEXT, *args,
                    **kwargs) -> NetworkResultAsync[Any]:
        try:
            async with getattr(self, method.lower())(url, *args, **kwargs) as response:
                text = await response.text()
                logger.debug(f"Response info: {response}")
                logger.debug(f"Content details: {text}")
                return NetworkResultAsync(
                    data=await getattr(response, res_method.lower())(),
                    code=response.status,
                    error=None,
                    response=response
                )
        except BaseException as error:
            logger.error(f"{type(error).__name__}: {str(error)}")
            if isinstance(error, HTTPException):
                return NetworkResultAsync(data=error.text, code=error.status_code, error=error, response=None)
            else:
                return NetworkResultAsync(data=None, code=ResponseCode.ERROR_OCCURRED_CODE, error=error, response=None)
