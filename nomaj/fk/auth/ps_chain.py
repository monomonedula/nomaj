from typing import List

from koda import Result, Ok, Err
from nomaj.fk.auth.identity import Identity, ANONYMOUS, is_anon
from nomaj.fk.auth.ps import Pass
from nomaj.nomaj import Req, Resp


class PsChain(Pass):
    def __init__(self, passes: List[Pass]):
        self._passes: List[Pass] = passes

    async def enter(self, request: Req) -> Result[Identity, Exception]:
        for p in self._passes:
            identity: Result[Identity, Exception] = await p.enter(request)
            if isinstance(identity, Err) or is_anon(identity.val):
                return identity
        return Ok(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Result[Resp, Exception]:
        r: Result[Resp, Exception] = Ok(response)
        for p in self._passes:
            if isinstance(r, Err):
                break
            r = await p.exit(r.val, identity)
        return r
