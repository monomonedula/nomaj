from nomaj.failable import Failable, Ok
from nomaj.http_exception import HttpException
from nomaj.nomaj import Nomaj, Req, Resp


class NjForward(Nomaj):
    def __init__(self, nj: Nomaj):
        self._nj: Nomaj = nj

    async def act_on(self, request: Req) -> Failable[Resp]:
        resp = await self._nj.act_on(request)
        if not resp.err():
            return resp
        err = resp.err()
        if isinstance(err, HttpException):
            return Ok(err.response)
        return resp
