from types import MappingProxyType
from typing import Dict, List
from urllib.parse import quote_plus, unquote_plus

from nomaj.fk.auth.codecs.codec import Codec
from nomaj.fk.auth.identity import Identity
from nomaj.failable import Failable, Ok, Err


class CcPlain(Codec):
    """Plain codec. Encodes identity as plain text"""

    def encode(self, identity: Identity) -> bytes:
        parts = [
            quote_plus(identity.urn),
            *[
                f";{key}={quote_plus(value)}"
                for key, value in identity.properties.items()
            ],
        ]
        return b"".join(p.encode() for p in parts)

    def decode(self, raw: bytes) -> Failable[Identity]:
        try:
            rawstr = raw.decode()
            props: Dict[str, str] = {}
            parts: List[str] = rawstr.split(";")
            for p in parts[1:]:
                k, v = p.split("=")
                props[k] = unquote_plus(v)
            return Ok(Identity(unquote_plus(parts[0]), MappingProxyType(props)))
        except Exception as e:
            return Err(e)
