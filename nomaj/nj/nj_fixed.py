from typing import Callable, Awaitable

from nomaj.failable import Failable, Ok
from nomaj.nomaj import Nomaj, Req, Resp


class NjFixed(Nomaj):
    def __init__(self, resp: Resp):
        self._resp: Failable[Resp] = Ok(resp)

    async def respond_to(self, request: Req) -> Failable[Resp]:
        return self._resp


class NjCallable(Nomaj):
    def __init__(self, cb: Callable[[Req], Awaitable[Failable[Resp]]]):
        self._cb: Callable[[Req], Awaitable[Failable[Resp]]] = cb

    async def respond_to(self, request: Req) -> Failable[Resp]:
        return await self._cb(request)
