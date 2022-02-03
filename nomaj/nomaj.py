from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import ParseResult

from multidict import MultiMapping

from nomaj.body import Body
from nomaj.failable import Failable


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
