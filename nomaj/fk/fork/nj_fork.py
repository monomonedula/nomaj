from typing import Tuple, Optional

from nomaj.failable import Failable, err_
from nomaj.fork import Fork
from nomaj.http_exception import HttpException
from nomaj.nomaj import Nomaj, Req, Resp
from nomaj.rs.rs_with_status import rs_with_status


class NjFork(Nomaj):
    def __init__(self, *forks: Fork):
        self._forks: Tuple[Fork, ...] = forks

    async def act_on(self, request: Req) -> Failable[Resp]:
        for fork in self._forks:
            nj: Failable[Optional[Nomaj]] = fork.route(request)
            if nj.err():
                return err_(nj)
            if nj.value() is not None:
                return await nj.value().act_on(request)
        raise HttpException(rs_with_status(404))
