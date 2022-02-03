from typing import Optional, Tuple

from nomaj.failable import Failable, Ok
from nomaj.fork import Fork
from nomaj.nomaj import Req, Nomaj


class FkChain(Fork):
    def __init__(self, *forks: Fork):
        self._forks: Tuple[Fork, ...] = forks

    def route(self, request: Req) -> Failable[Optional[Nomaj]]:
        for fork in self._forks:
            rs = fork.route(request)
            if rs.err():
                return rs
            if rs.value() is not None:
                return rs
        return Ok(None)
