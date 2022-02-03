from typing import Optional

from nomaj.failable import Failable, Ok, err_
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.nj_auth import NjAuth
from nomaj.fk.auth.rq_auth import RqAuth, rq_authenticated
from nomaj.fork import Fork
from nomaj.nomaj import Req, Nomaj


class FkAuthenticated(Fork):
    def __init__(self, nj: Nomaj, header: str = NjAuth.__name__):
        self._nj: Nomaj = nj
        self._header: str = header

    def route(self, request: Req) -> Failable[Optional[Nomaj]]:
        f = rq_authenticated(request, self._header)
        if f.err():
            return err_(f)
        if f.value() == ANONYMOUS:
            return Ok(None)
        return Ok(self._nj)
