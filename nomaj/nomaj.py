from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict
from urllib.parse import ParseResult

from multidict import MultiMapping, CIMultiDictProxy, CIMultiDict
from nvelope import JSON

from nomaj.body import Body, EmptyBody
from koda import Result


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
    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        pass

    @abstractmethod
    def meta(self) -> Dict[str, JSON]:
        pass
