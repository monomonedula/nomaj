from dataclasses import dataclass
from typing import Mapping
from types import MappingProxyType


@dataclass(frozen=True)
class Identity:
    urn: str
    properties: Mapping[str, str] = MappingProxyType({})


ANONYMOUS = Identity("")


def is_anon(idt: Identity) -> bool:
    return idt.urn == ""
