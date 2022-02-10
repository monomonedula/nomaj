from typing import Optional, Tuple

from koda import Result, Ok, Err

from nomaj.fork import Fork
from nomaj.nomaj import Req, Nomaj


class FkChain(Fork):
    def __init__(self, *forks: Fork):
        self._forks: Tuple[Fork, ...] = forks

    def route(self, request: Req) -> Result[Optional[Nomaj], Exception]:
        for fork in self._forks:
            rs = fork.route(request)
            if isinstance(rs, Err) or rs.val is not None:
                return rs
        return Ok(None)
