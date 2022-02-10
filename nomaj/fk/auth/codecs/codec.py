from abc import ABC, abstractmethod

from koda import Result

from nomaj.fk.auth.identity import Identity


class Codec(ABC):
    @abstractmethod
    def encode(self, identity: Identity) -> bytes:
        pass

    @abstractmethod
    def decode(self, raw: bytes) -> Result[Identity, Exception]:
        pass
