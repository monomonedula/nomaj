from koda import Result, Err, Ok

from nomaj.fk.auth.identity import is_anon
from nomaj.fk.auth.nj_auth import NjAuth
from nomaj.fk.auth.rq_auth import rq_authenticated, RqAuth
from nomaj.http_exception import HttpException
from nomaj.nomaj import Nomaj, Req, Resp


class NjSecure(Nomaj):
    def __init__(self, nm: Nomaj, header: str = NjAuth.__name__):
        self._nm: Nomaj = nm
        self._header: str = header

    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        rq: Result[RqAuth, Exception] = rq_authenticated(request, self._header)
        if isinstance(rq, Err):
            return rq
        if is_anon(rq.val.identity):
            return Err(HttpException.from_status(401))
        return await self._nm.respond_to(request)
