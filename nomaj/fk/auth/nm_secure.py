from nomaj.fk.auth.identity import ANONYMOUS
from nomaj.fk.auth.nm_auth import NmAuth
from nomaj.fk.auth.rq_auth import rq_authenticated
from nomaj.http_exception import HttpException
from nomaj.maybe import Maybe, err_, Err
from nomaj.nomaj import Nomaj, Req, Resp


class NmSecure(Nomaj):
    def __init__(self, nm: Nomaj, header: str = NmAuth.__name__):
        self._nm: Nomaj = nm
        self._header: str = header

    async def act_on(self, request: Req) -> Maybe[Resp]:
        rq = rq_authenticated(request, self._header)
        if rq.err():
            return err_(rq)
        if rq.value() == ANONYMOUS:
            return Err(HttpException(303))
        return await self._nm.act_on(request)
