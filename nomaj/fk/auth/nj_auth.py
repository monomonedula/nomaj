from typing import Optional

from koda import Result, Err

from nomaj.fk.auth.identity import Identity, is_anon
from nomaj.fk.auth.ps import Pass
from nomaj.fk.auth.rq_auth import rq_with_auth
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

    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        user: Result[Identity, Exception] = await self._pass.enter(request)
        if isinstance(user, Err):
            return user
        if is_anon(user.val):
            return await self.act_identified_on(request, user.val)
        return await self._nm.respond_to(rq_without_headers(request, [self._header]))

    async def act_identified_on(
        self, request: Req, identity: Identity
    ) -> Result[Resp, Exception]:
        response = await self._nm.respond_to(
            rq_with_auth(
                identity=identity,
                header=self._header,
                rq=rq_without_headers(request, [self._header]),
            )
        )
        if isinstance(response, Err):
            return response
        return await self._pass.exit(
            response=response.val,
            identity=identity,
        )

    def meta(self) -> Dict[str, JSON]:
        return {
            "nomaj": {
                "type": self.__class__.__name__,
                "pass": self._pass.meta(),
            },
            "children": [],
        }
