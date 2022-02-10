from koda import Result, Ok
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.ps import Pass
from nomaj.nomaj import Req, Resp


class PsLogout(Pass):
    async def enter(self, request: Req) -> Result[Identity, Exception]:
        return Ok(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Result[Resp, Exception]:
        return Ok(response)
