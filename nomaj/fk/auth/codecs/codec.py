from abc import ABC, abstractmethod

from nomaj.fk.auth.identity import Identity
from nomaj.maybe import Maybe


class Codec(ABC):
    @abstractmethod
    def encode(self, identity: Identity) -> str:
        pass

    @abstractmethod
    def decode(self, raw: str) -> Maybe[Identity]:
        pass
