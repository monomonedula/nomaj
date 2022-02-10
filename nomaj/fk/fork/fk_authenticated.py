from typing import Optional

from koda import Result, Ok, Err
from nomaj.fk.auth.identity import is_anon
from nomaj.fk.auth.nj_auth import NjAuth
from nomaj.fk.auth.rq_auth import rq_authenticated
from nomaj.fork import Fork
from nomaj.nomaj import Req, Nomaj


class FkAuthenticated(Fork):
    def __init__(self, nj: Nomaj, header: str = NjAuth.__name__):
        self._nj: Nomaj = nj
        self._header: str = header

    def route(self, request: Req) -> Result[Optional[Nomaj], Exception]:
        f = rq_authenticated(request, self._header)
        if isinstance(f, Err):
            return f
        if is_anon(f.val.identity):
            return Ok(None)
        return Ok(self._nj)
