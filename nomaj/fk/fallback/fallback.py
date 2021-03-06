import dataclasses
import logging
from logging import Logger
from typing import Optional, Dict
import http.client
from abc import ABC, abstractmethod

from koda import Result, Ok, Err
from nvelope import JSON

from nomaj.http_exception import HttpException
from nomaj.nomaj import Req, Resp, Nomaj
from nomaj.rs.rs_text import rs_text
from nomaj.rs.rs_with_status import rs_with_status


@dataclasses.dataclass(frozen=True)
class ReqFallback:
    req: Req
    err: Exception
    suggested_code: int


class Fallback(ABC):
    @abstractmethod
    async def route(self, req: ReqFallback) -> Result[Optional[Resp], Exception]:
        pass

    @abstractmethod
    def meta(self) -> Dict[str, JSON]:
        pass


class NjFallback(Nomaj):
    def __init__(self, nj: Nomaj, fb: Fallback):
        self._nj: Nomaj = nj
        self._fb: Fallback = fb

    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        resp: Result[Resp, Exception] = await self._nj.respond_to(request)
        if isinstance(resp, Err):
            err = resp.val
            if isinstance(err, HttpException):
                code = err.response.status
            else:
                code = 500
            fb_resp = await self._fb.route(ReqFallback(request, err, code))
            if not isinstance(fb_resp, Err) and fb_resp.val:
                resp = Ok(fb_resp.val)
        return resp

    def meta(self) -> Dict[str, JSON]:
        return {
            "nomaj": {"type": self.__class__.__name__, "fallback": self._fb.meta()},
            "children": [self._nj.meta()],
        }


class FbStatus(Fallback):
    async def route(self, req: ReqFallback) -> Result[Optional[Resp], Exception]:
        t = http.client.responses[req.suggested_code]
        return Ok(
            rs_text(
                f"{req.suggested_code} {t}", response=rs_with_status(req.suggested_code)
            )
        )

    def meta(self) -> Dict[str, JSON]:
        return {
            "fallback": {
                "type": self.__class__.__name__,
            }
        }


class FbLog(Fallback):
    def __init__(
        self,
        fb: Fallback,
        logger: Logger = logging.getLogger(__name__),
        level: int = logging.ERROR,
    ):
        self._logger: Logger = logger
        self._level: int = level
        self._fb: Fallback = fb

    async def route(self, req: ReqFallback) -> Result[Optional[Resp], Exception]:
        resp = await self._fb.route(req)
        self._logger.log(
            self._level,
            f"Handled error: {req.err!r} caused by {req.req!r}. Result: {resp!r}",
        )
        return resp

    def meta(self) -> Dict[str, JSON]:
        return {
            "fallback": {
                "type": self.__class__.__name__,
            }
        }
