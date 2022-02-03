from typing import List

from nomaj.failable import Failable, Ok
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.ps import Pass
from nomaj.nomaj import Req, Resp


class PsChain(Pass):
    def __init__(self, passes: List[Pass]):
        self._passes: List[Pass] = passes

    async def enter(self, request: Req) -> Failable[Identity]:
        for p in self._passes:
            identity: Failable[Identity] = await p.enter(request)
            if identity.err() or identity.value() != ANONYMOUS:
                return identity
        return Ok(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        r = Ok(response)
        for p in self._passes:
            r = await p.exit(r.value(), identity)
            if r.err():
                break
        return r
