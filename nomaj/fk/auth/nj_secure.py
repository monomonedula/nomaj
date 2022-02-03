from nomaj.fk.auth.identity import ANONYMOUS
from nomaj.fk.auth.nj_auth import NjAuth
from nomaj.fk.auth.rq_auth import rq_authenticated
from nomaj.http_exception import HttpException
from nomaj.failable import Failable, err_, Err
from nomaj.nomaj import Nomaj, Req, Resp


class NjSecure(Nomaj):
    def __init__(self, nm: Nomaj, header: str = NjAuth.__name__):
        self._nm: Nomaj = nm
        self._header: str = header

    async def act_on(self, request: Req) -> Failable[Resp]:
        rq = rq_authenticated(request, self._header)
        if rq.err():
            return err_(rq)
        if rq.value() == ANONYMOUS:
            return Err(HttpException.from_status(401))
        return await self._nm.act_on(request)
