from typing import Optional

from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.ps import Pass
from nomaj.fk.auth.rq_auth import rq_with_auth
from nomaj.failable import Failable, err_
from nomaj.nomaj import Nomaj, Req, Resp
from nomaj.rq.rq_without_headers import rq_without_headers


class NjAuth(Nomaj):
    """
    Authenticating muggle.
    """

    def __init__(self, nm: Nomaj, pss: Pass, header: Optional[str] = None):
        self._nm: Nomaj = nm
        self._pass: Pass = pss
        self._header: str = header or self.__class__.__name__

    async def act_on(self, request: Req) -> Failable[Resp]:
        user: Failable[Identity] = await self._pass.enter(request)
        if user.err():
            return err_(user)
        if user != ANONYMOUS:
            return await self.act_identified_on(request, user.value())
        return await self._nm.act_on(rq_without_headers(request, [self._header]))

    async def act_identified_on(
        self, request: Req, identity: Identity
    ) -> Failable[Resp]:
        response = await self._nm.act_on(
            rq_with_auth(
                identity=identity,
                header=self._header,
                rq=rq_without_headers(request, [self._header]),
            )
        )
        if response.err():
            return err_(response)
        return await self._pass.exit(
            response=response.value(),
            identity=identity,
        )
