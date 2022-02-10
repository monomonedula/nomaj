from typing import Optional

from koda import Result, Ok
from nomaj.fork import Fork
from nomaj.nomaj import Nomaj, Req


class FkFixed(Fork):
    def __init__(self, nj: Nomaj):
        self._nj: Nomaj = nj

    def route(self, request: Req) -> Result[Optional[Nomaj], Exception]:
        return Ok(self._nj)
