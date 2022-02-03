from nomaj.failable import Failable
from nomaj.fk.auth.codecs.codec import Codec
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.signature import Signature


class CcSigned(Codec):
    def __init__(self, codec: Codec, signature: Signature):
        self._origin: Codec = codec
        self._signature: Signature = signature

    def encode(self, identity: Identity) -> bytes:
        raw: bytes = self._origin.encode(identity)
        return b"".join((raw, self._signature.sign(raw)))

    def decode(self, bts: bytes) -> Failable[Identity]:
        length = self._signature.length()
        signature: bytes = bts[-length:]
        raw: bytes = bts[:-length]
        if signature == self._signature.sign(raw):
            return self._origin.decode(raw)
        return ANONYMOUS
