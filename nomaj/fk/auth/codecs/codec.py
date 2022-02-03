from abc import ABC, abstractmethod

from nomaj.fk.auth.identity import Identity
from nomaj.failable import Failable


class Codec(ABC):
    @abstractmethod
    def encode(self, identity: Identity) -> str:
        pass

    @abstractmethod
    def decode(self, raw: str) -> Failable[Identity]:
        pass
