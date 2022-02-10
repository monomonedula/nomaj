from typing import Tuple, Optional

from koda import Result, Err
from nomaj.fork import Fork
from nomaj.http_exception import HttpException
from nomaj.nomaj import Nomaj, Req, Resp
from nomaj.rs.rs_with_status import rs_with_status


class NjFork(Nomaj):
    def __init__(self, *forks: Fork):
        self._forks: Tuple[Fork, ...] = forks

    async def respond_to(self, request: Req) -> Result[Resp, Exception]:
        for fork in self._forks:
            nj: Result[Optional[Nomaj], Exception] = fork.route(request)
            if isinstance(nj, Err):
                return nj
            if nj.val is not None:
                return await nj.val.respond_to(request)
        return Err(HttpException(rs_with_status(404)))
