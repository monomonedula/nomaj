from typing import Callable, Awaitable

from koda import Result, Ok
from nomaj.nomaj import Nomaj, Req, Resp


class NjFixed(Nomaj):
    def __init__(self, resp: Resp):
        self._resp: Result[Resp, Exception] = Ok(resp)

    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        return self._resp


class NjCallable(Nomaj):
    def __init__(self, cb: Callable[[Req], Awaitable[Result[Resp, Exception]]]):
        self._cb: Callable[[Req], Awaitable[Result[Resp, Exception]]] = cb

    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        return await self._cb(request)
