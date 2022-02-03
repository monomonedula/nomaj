from nomaj.failable import Failable, Ok
from nomaj.fk.auth.identity import Identity
from nomaj.fk.auth.ps import Pass
from nomaj.nomaj import Req, Resp


class PsFixed(Pass):
    def __init__(self, idt: Identity):
        self._idt: Failable[Identity] = Ok(idt)

    async def enter(self, request: Req) -> Failable[Identity]:
        return self._idt

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        return Ok(response)
