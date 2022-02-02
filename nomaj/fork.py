from abc import ABC, abstractmethod
from typing import Optional

from nomaj.maybe import Maybe
from nomaj.nomaj import Req, Nomaj


class Fork(ABC):
    @abstractmethod
    def route(self, request: Req) -> Maybe[Optional[Nomaj]]:
        pass


