import asyncio
import io
from abc import ABC, abstractmethod
from typing import Union, Optional, Callable, Awaitable, Dict, Any, AsyncIterator


class Body(ABC):
    @abstractmethod
    async def read(self, nbytes: Optional[int] = None) -> bytes:
        pass


class BodyOf(Body):
    def __init__(self, s: Union[str, bytes]):
        self._s: io.BytesIO = io.BytesIO(s if isinstance(s, bytes) else s.encode())

    async def read(self, nbytes: Optional[int] = None) -> bytes:
        return self._s.read1(nbytes)


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
