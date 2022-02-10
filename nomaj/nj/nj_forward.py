from koda import Result, Ok

from nomaj.http_exception import HttpException
from nomaj.nomaj import Nomaj, Req, Resp


class NjForward(Nomaj):
    def __init__(self, nj: Nomaj):
        self._nj: Nomaj = nj

    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        resp = await self._nj.respond_to(request)
        if isinstance(resp, Ok):
            return resp
        err = resp.val
        if isinstance(err, HttpException):
            return Ok(err.response)
        return resp
