from abc import ABC, abstractmethod
from typing import Optional

from nomaj.failable import Failable
from nomaj.nomaj import Req, Nomaj


class Fork(ABC):
    @abstractmethod
    def route(self, request: Req) -> Failable[Optional[Nomaj]]:
        pass
