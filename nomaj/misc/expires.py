from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import cast

import babel
from babel.dates import format_datetime


class Expires(ABC):
    """
    Expiration date in GMT
    """

    @abstractmethod
    async def print(self) -> str:
        """
        String representation of expiration time.
        :return: Representation of expiration time
        """
        pass


class Date(Expires):
    def __init__(
        self,
        expires: datetime,
        pattern: str = "'Expires='EEE, dd MMM yyyy HH:mm:ss 'GMT'",
        locale: babel.Locale = babel.Locale("en"),
    ):
        self._pattern: str = pattern
        self._locale: babel.Locale = locale
        self._expires: datetime = expires

    async def print(self) -> str:
        return cast(
            str, format_datetime(self._expires, self._pattern, locale=self._locale)
        )


class Never(Expires):
    """
    Never expires.
    """

    def __init__(self):
        self._origin: Expires = Date(datetime.utcnow() + timedelta(weeks=1500))

    async def print(self) -> str:
        return await self._origin.print()


class Expired(Expires):
    """
    Already expired. Returns "0" according to RFC7234.
    """

    def __init__(self):
        self._origin: Expires = Date(datetime.utcfromtimestamp(0.0))

    async def print(self) -> str:
        return await self._origin.print()
