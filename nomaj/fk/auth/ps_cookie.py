from datetime import datetime, timedelta
from typing import Optional

from koda import Result, Ok

from nomaj.fk.auth.codecs.codec import Codec
from nomaj.fk.auth.identity import Identity, ANONYMOUS, is_anon
from nomaj.fk.auth.ps import Pass
from nomaj.misc.cookies import cookies_of
from nomaj.misc.expires import Date
from nomaj.nomaj import Req, Resp
from nomaj.rs.rs_with_cookie import rs_with_cookie


class PsCookie(Pass):
    """
    Pass via cookie information.

    :param codec: a codec to encode identities.
    :param name: cookie name. Default to `PsCookie`.
    :param days: cookie expiration time in days. Default to 30 days
    """

    def __init__(self, codec: Codec, name: Optional[str] = None, days: int = 30):
        self._codec: Codec = codec
        self._name: str = (name or self.__class__.__name__).strip()
        self._days: int = days

    async def enter(self, request: Req) -> Result[Identity, Exception]:
        value: Optional[str] = cookies_of(request).get(self._name)
        if value is not None:
            return self._codec.decode(value.encode())
        return Ok(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Result[Resp, Exception]:
        """
        Adds authentication cookie to the response
        """
        if is_anon(identity):
            text = ""
        else:
            text = self._codec.encode(identity).decode()
        return Ok(
            rs_with_cookie(
                response,
                self._name,
                text,
                "Path=/",
                "HttpOnly",
                await Date(
                    datetime.utcnow() + timedelta(days=self._days),
                ).print(),
            )
        )
