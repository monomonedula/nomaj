import base64
from abc import ABC, abstractmethod

from nomaj.failable import Failable, Ok
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.ps import Pass
from nomaj.nomaj import Req, Resp


class Entry(ABC):
    @abstractmethod
    async def enter(self, user: str, password: str) -> Failable[Identity]:
        pass


class PsBasic(Pass):
    def __init__(self, realm: str, basic: Entry):
        self._realm: str = realm
        self._entry: Entry = basic

    async def enter(self, request: Req) -> Failable[Identity]:
        if (
            "authorization" not in request.headers
            or "Basic" not in request.headers["authorization"]
        ):
            identity = ANONYMOUS
        else:
            auth: str = base64.b64decode(
                request.headers["authorization"].split("Basic")[1].strip()
            ).decode()
            user, password = auth.split(":", maxsplit=1)
            identity: Failable[Identity] = await self._entry.enter(user, password)
        return identity

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        return Ok(response)
