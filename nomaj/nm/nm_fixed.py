from nomaj.failable import Failable, Just
from nomaj.nomaj import Nomaj, Req, Resp


class NmFixed(Nomaj):
    def __init__(self, resp: Resp):
        self._resp: Failable[Resp] = Just(resp)

    async def act_on(self, request: Req) -> Failable[Resp]:
        return self._resp
