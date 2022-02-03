from types import MappingProxyType
from typing import Dict, List
from urllib.parse import quote_plus, unquote_plus

from nomaj.fk.auth.codecs.codec import Codec
from nomaj.fk.auth.identity import Identity
from nomaj.failable import Failable, Just, Err


class CcPlain(Codec):
    """Plain codec. Encodes identity as plain text"""

    def encode(self, identity: Identity) -> str:
        parts = [
            quote_plus(identity.urn),
            *[
                f";{key}={quote_plus(value)}"
                for key, value in identity.properties.items()
            ],
        ]
        return "".join(parts)

    def decode(self, raw: str) -> Failable[Identity]:
        try:
            props: Dict[str, str] = {}
            parts: List[str] = raw.split(";")
            for p in parts[1:]:
                k, v = p.split("=")
                props[k] = unquote_plus(v)
            return Just(Identity(unquote_plus(parts[0]), MappingProxyType(props)))
        except Exception as e:
            return Err(e)
