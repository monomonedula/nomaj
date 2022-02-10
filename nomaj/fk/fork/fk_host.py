from typing import Optional

from koda import Result, Ok
from nomaj.fork import Fork
from nomaj.nomaj import Nomaj, Req


class FkHost(Fork):
    def __init__(self, host: str, nj: Nomaj):
        self._host: str = host
        self._nj: Nomaj = nj

    def route(self, request: Req) -> Result[Optional[Nomaj], Exception]:
        if request.headers.get("host") == self._host:
            return Ok(self._nj)
        return Ok(None)
