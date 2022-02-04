import dataclasses
from typing import Optional

from mypy.typeshed.stdlib.abc import ABC, abstractmethod

from nomaj.failable import Failable
from nomaj.http_exception import HttpException
from nomaj.nomaj import Req, Resp, Nomaj


@dataclasses.dataclass(frozen=True)
class ReqFallback:
    req: Req
    err: Exception
    suggested_code: int


class Fallback(ABC):
    @abstractmethod
    async def route(self, req: ReqFallback) -> Failable[Optional[Resp]]:
        pass


class NjFallback(Nomaj):
    def __init__(self, nj: Nomaj, fb: Fallback):
        self._nj: Nomaj = nj
        self._fb: Fallback = fb

    async def respond_to(self, request: Req) -> Failable[Resp]:
        resp = await self._nj.respond_to(request)
        if resp.err():
            err = resp.err()
            if isinstance(err, HttpException):
                code = err.response.status
            else:
                code = 500
            resp = await self._fb.route(ReqFallback(request, resp.err(), code))
        return resp
