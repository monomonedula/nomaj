from typing import Optional

from nomaj.failable import Failable, Ok
from nomaj.fork import Fork
from nomaj.nomaj import Nomaj, Req


class FkFixed(Fork):
    def __init__(self, nj: Nomaj):
        self._nj: Nomaj = nj

    def route(self, request: Req) -> Failable[Optional[Nomaj]]:
        return Ok(self._nj)
