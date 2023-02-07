import datetime as date
import math
from typing import Final

from dateutil import tz
from datetime import datetime

UTC_ZONE: Final = tz.UTC
LOCAL_ZONE: Final = tz.tzlocal()

SECONDS_IN_MINUTE: Final[int] = 60
SECONDS_IN_HOUR: Final[int] = int(math.pow(SECONDS_IN_MINUTE, 2))
SECONDS_IN_DAY: Final[int] = SECONDS_IN_HOUR * 24
SECONDS_IN_WEEK: Final[int] = SECONDS_IN_DAY * 7


def utc_to_local(utc_time: date.datetime) -> date.datetime:
    utc_time = utc_time.replace(tzinfo=UTC_ZONE)
    return utc_time.astimezone(LOCAL_ZONE)


def from_timestamp_delta(delta: float) -> datetime:
    return datetime.fromtimestamp(datetime.utcnow().timestamp() + delta)


def with_delta(*args, **kwargs) -> datetime:
    """
    Arguments:
        days: float — days delta\n
        seconds: float — seconds delta\n
        microseconds: float — microseconds delta\n
        milliseconds: float — milliseconds delta\n
        minutes: float = — minutes delta\n
        hours: float = — hours delta\n
        weeks: float = — weeks delta\n
        *,\n
        fold: int = — fold\n
    :return: datetime object with specified delta
    :rtype: :class: datetime
    """
    return datetime.utcnow() + date.timedelta(*args, **kwargs)


def int_timestamp(_date: datetime) -> int:
    return int(_date.timestamp())
