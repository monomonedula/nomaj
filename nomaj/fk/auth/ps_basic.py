import base64
from abc import ABC, abstractmethod

from koda import Result, Ok
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.ps import Pass
from nomaj.nomaj import Req, Resp


class Entry(ABC):
    @abstractmethod
    async def enter(self, user: str, password: str) -> Result[Identity, Exception]:
        pass


class PsBasic(Pass):
    def __init__(self, realm: str, basic: Entry):
        self._realm: str = realm
        self._entry: Entry = basic

    async def enter(self, request: Req) -> Result[Identity, Exception]:
        identity: Result[Identity, Exception]
        if (
            "authorization" not in request.headers
            or "Basic" not in request.headers["authorization"]
        ):
            identity = Ok(ANONYMOUS)
        else:
            auth: str = base64.b64decode(
                request.headers["authorization"].split("Basic")[1].strip()
            ).decode()
            user, password = auth.split(":", maxsplit=1)
            identity = await self._entry.enter(user, password)
        return identity

    async def exit(self, response: Resp, identity: Identity) -> Result[Resp, Exception]:
        return Ok(response)
