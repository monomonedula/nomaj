from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import ParseResult

from multidict import MultiMapping, CIMultiDictProxy, CIMultiDict

from nomaj.body import Body, EmptyBody
from nomaj.failable import Failable


@dataclass(frozen=True)
class Resp:
    status: int
    headers: MultiMapping[str] = CIMultiDictProxy(CIMultiDict())
    body: Body = EmptyBody()


@dataclass(frozen=True)
class Req:
    uri: ParseResult
    headers: MultiMapping[str]
    method: str
    body: Body


class Nomaj(ABC):
    @abstractmethod
    async def respond_to(self, request: Req) -> Failable[Resp]:
        pass
