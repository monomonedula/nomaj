from typing import List

from nomaj.failable import Failable
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.ps import Pass
from nomaj.nomaj import Req, Resp


class PsAll(Pass):
    def __init__(self, passes: List[Pass], identity: int):
        if identity not in range(len(passes)):
            raise ValueError(
                f"Bad identity index ({identity}) for a list of {len(passes)} passes"
            )
        self._passes: List[Pass] = passes
        self._index: int = identity

    async def enter(self, request: Req) -> Failable[Identity]:
        identities: List[Failable[Identity]] = []
        for p in self._passes:
            identity: Failable[Identity] = await p.enter(request)
            if identity.err() or identity.value() == ANONYMOUS:
                return identity
            identities.append(identity)
        return identities[self._index]

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        return await self._passes[self._index].exit(response, identity)
