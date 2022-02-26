from abc import ABC, abstractmethod
from typing import Optional, Dict

from koda import Result
from nvelope import JSON

from nomaj.nomaj import Req, Nomaj


class Fork(ABC):
    @abstractmethod
    def route(self, request: Req) -> Result[Optional[Nomaj], Exception]:
        pass

    @abstractmethod
    def meta(self) -> Dict[str, JSON]:
        pass
