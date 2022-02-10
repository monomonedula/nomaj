from abc import ABC, abstractmethod
from typing import Optional

from koda import Result

from nomaj.nomaj import Req, Nomaj


class Fork(ABC):
    @abstractmethod
    def route(self, request: Req) -> Result[Optional[Nomaj], Exception]:
        pass
