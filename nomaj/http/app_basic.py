import io
import asyncio
from typing import Callable, Awaitable, Dict, Any, AsyncIterator, Optional, Union
from multidict import CIMultiDict, CIMultiDictProxy

from nomaj.http_exception import HttpException
from nomaj.failable import Failable
from nomaj.nomaj import Nomaj, Req, Resp, Body


class AppBasic:
    def __init__(self, nomaj: Nomaj):
        self._nomaj: Nomaj = nomaj

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        elif scope["type"] == "http":
            maybe_resp: Failable[Resp] = await self._nomaj.act_on(
                Req(
                    uri=scope["path"],
                    method=scope["method"],
                    headers=CIMultiDictProxy(
                        CIMultiDict(
                            [(k.decode(), v.decode()) for k, v in scope["headers"]]
                        )
                    ),
                    body=BodyFromASGI(receive),
                )
            )
            if err := maybe_resp.err():
                resp = (
                    err.response
                    if isinstance(err, HttpException)
                    else Resp(
                        status=500,
                        headers=CIMultiDict(),
                        body=EmptyBody(),
                    )
                )
            else:
                resp = maybe_resp
            await _respond(resp, send)


async def _respond(response: Resp, send):
    await send(
        {
            "type": "http.response.start",
            "status": response.status,
            "headers": [
                (name.encode(), value.encode())
                for name, value in response.headers.items()
            ],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": await response.body.read(),
            "more_body": False,
        }
    )


class EmptyBody(Body):
    async def read(self, nbytes: Optional[int] = None) -> bytes:
        return b""


class BodyFromASGI(Body):
    def __init__(self, receive: Callable[[], Awaitable[Dict[str, Any]]]):
        self._receive: Callable[[], Awaitable[Dict[str, Any]]] = receive
        self._empty: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()
        self._leftover: bytearray = bytearray()

    async def read(self, nbytes: Optional[int] = None) -> bytes:
        async with self._lock:
            buff = bytearray(nbytes)
            async for chunk in self._chunks(nbytes):
                buff.extend(chunk)
            if len(buff) > nbytes:
                self._leftover = buff[nbytes:]
            return bytes(buff)

    async def _chunks(self, nbytes: Optional[int]) -> AsyncIterator[bytes]:
        bytescount = 0
        if self._leftover:
            bts = bytes(self._leftover)
            self._leftover = bytearray()
            yield bts
        while not self._empty and (nbytes is None or nbytes > bytescount):
            message = await self._receive()
            body = message.get("body")
            self._empty = not message.get("more_body", False)
            if body is not None:
                bytescount += len(body)
                yield body


class BodyFromIterable(Body):
    def __init__(self, it: AsyncIterator[bytes]):
        self._it: AsyncIterator[bytes] = it
        self._empty: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()
        self._leftover: bytearray = bytearray()

    async def read(self, nbytes: Optional[int] = None) -> bytes:
        async with self._lock:
            buff = bytearray(nbytes)
            async for chunk in self._it:
                buff.extend(chunk)
            if len(buff) > nbytes:
                self._leftover = buff[nbytes:]
            return bytes(buff)

    async def _chunks(self, nbytes: Optional[int]) -> AsyncIterator[bytes]:
        bytescount = 0
        if self._leftover:
            bts = bytes(self._leftover)
            self._leftover = bytearray()
            yield bts
        async for chunk in self._it:
            bytescount += len(chunk)
            yield chunk
            if nbytes or nbytes > bytescount:
                break


class BodyOf(Body):
    def __init__(self, s: Union[str, bytes]):
        self._s: io.BytesIO = io.BytesIO(s if isinstance(s, bytes) else s.encode())

    async def read(self, nbytes: Optional[int] = None) -> bytes:
        return self._s.read1(nbytes)
