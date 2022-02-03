from abc import ABC, abstractmethod

from nomaj.fk.auth.identity import Identity
from nomaj.failable import Failable


class Codec(ABC):
    @abstractmethod
    def encode(self, identity: Identity) -> bytes:
        pass

    @abstractmethod
    def decode(self, raw: bytes) -> Failable[Identity]:
        pass
