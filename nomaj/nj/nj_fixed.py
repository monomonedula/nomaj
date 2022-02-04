from nomaj.failable import Failable, Ok
from nomaj.nomaj import Nomaj, Req, Resp


class NjFixed(Nomaj):
    def __init__(self, resp: Resp):
        self._resp: Failable[Resp] = Ok(resp)

    async def respond_to(self, request: Req) -> Failable[Resp]:
        return self._resp
