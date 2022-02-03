from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from urllib.parse import ParseResult

from multidict import MultiMapping

from nomaj.failable import Failable


class Body(ABC):
    @abstractmethod
    async def read(self, nbytes: Optional[int] = None) -> bytes:
        pass


@dataclass(frozen=True)
class Resp:
    status: int
    headers: MultiMapping[str]
    body: Body


@dataclass(frozen=True)
class Req:
    uri: ParseResult
    headers: MultiMapping[str]
    method: str
    body: Body


class Nomaj(ABC):
    @abstractmethod
    async def act_on(self, request: Req) -> Failable[Resp]:
        pass
