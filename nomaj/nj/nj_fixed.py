from typing import Callable, Awaitable, Dict

from koda import Result, Ok
from nvelope import JSON

from nomaj.nomaj import Nomaj, Req, Resp


class NjFixed(Nomaj):
    def __init__(self, resp: Resp):
        self._resp: Ok[Resp] = Ok(resp)

    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        return self._resp

    def meta(self) -> Dict[str, JSON]:
        return {
            "nomaj": {
                "type": self.__class__.__name__,
            },
            "response": {
                "status": self._resp.val.status,
                "headers": list(self._resp.val.headers.items()),
            },
        }


class NjCallable(Nomaj):
    def __init__(self, cb: Callable[[Req], Awaitable[Result[Resp, Exception]]]):
        self._cb: Callable[[Req], Awaitable[Result[Resp, Exception]]] = cb

    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        return await self._cb(request)

    def meta(self) -> Dict[str, JSON]:
        return {
            "nomaj": {
                "type": self.__class__.__name__,
            },
        }


class NjWithMeta(Nomaj):
    def __init__(self, nj: Nomaj, meta: Dict[str, JSON]):
        self._nj: Nomaj = nj
        self._meta: Dict[str, JSON] = meta

    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        return await self._nj.respond_to(request)

    def meta(self) -> Dict[str, JSON]:
        return self._meta
