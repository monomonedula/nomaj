from nomaj.maybe import Maybe, Just
from nomaj.nomaj import Nomaj, Req, Resp


class NmFixed(Nomaj):
    def __init__(self, resp: Resp):
        self._resp: Maybe[Resp] = Just(resp)

    async def act_on(self, request: Req) -> Maybe[Resp]:
        return self._resp

