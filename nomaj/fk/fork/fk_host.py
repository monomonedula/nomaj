from typing import Optional

from nomaj.failable import Failable, Ok
from nomaj.fork import Fork
from nomaj.nomaj import Nomaj, Req


class FkHost(Fork):
    def __init__(self, host: str, nj: None):
        self._host: str = host
        self._nj: Nomaj = nj

    def route(self, request: Req) -> Failable[Optional[Nomaj]]:
        if request.headers.get("host") == self._host:
            return Ok(self._nj)
        return Ok(None)
