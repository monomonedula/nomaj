from koda import Result, Ok
from nomaj.fk.auth.identity import Identity
from nomaj.fk.auth.ps import Pass
from nomaj.nomaj import Req, Resp


class PsFixed(Pass):
    def __init__(self, idt: Identity):
        self._idt: Result[Identity, Exception] = Ok(idt)

    async def enter(self, request: Req) -> Result[Identity, Exception]:
        return self._idt

    async def exit(self, response: Resp, identity: Identity) -> Result[Resp, Exception]:
        return Ok(response)
