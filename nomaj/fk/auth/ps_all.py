from typing import List

from koda import Result, Err

from nomaj.fk.auth.identity import Identity, ANONYMOUS, is_anon
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

    async def enter(self, request: Req) -> Result[Identity, Exception]:
        identities: List[Result[Identity, Exception]] = []
        for p in self._passes:
            identity: Result[Identity, Exception] = await p.enter(request)
            if isinstance(identity, Err) or is_anon(identity.val):
                return identity
            identities.append(identity)
        return identities[self._index]

    async def exit(self, response: Resp, identity: Identity) -> Result[Resp, Exception]:
        return await self._passes[self._index].exit(response, identity)
