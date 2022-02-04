from nomaj.failable import Failable, Ok
from nomaj.http_exception import HttpException
from nomaj.nomaj import Nomaj, Req, Resp


class NjForward(Nomaj):
    def __init__(self, nj: Nomaj):
        self._nj: Nomaj = nj

    async def respond_to(self, request: Req) -> Failable[Resp]:
        resp = await self._nj.respond_to(request)
        if not resp.err():
            return resp
        err = resp.err()
        if isinstance(err, HttpException):
            return Ok(err.response)
        return resp
