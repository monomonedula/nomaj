import re
from typing import Union, Pattern, Optional

from nomaj.failable import Failable, Ok
from nomaj.fork import Fork
from nomaj.nj.nj_fixed import NjFixed
from nomaj.nomaj import Nomaj, Resp, Req
from nomaj.rs.rs_text import rs_text


class FkRegex(Fork):
    def __init__(self, pattern: Union[str, Pattern], *, resp: Union[Nomaj, Resp, str]):
        self._pattern: Pattern = (
            pattern if isinstance(pattern, re.Pattern) else re.compile(pattern)
        )
        self._nj: Nomaj
        if isinstance(resp, str):
            self._nj = NjFixed(rs_text(resp))
        elif isinstance(resp, Resp):
            self._nj = NjFixed(resp)
        elif isinstance(resp, Nomaj):
            self._nj = resp
        else:
            raise TypeError("Expected Response, Muggle or str. Got: %r" % type(resp))

    def route(self, request: Req) -> Failable[Optional[Nomaj]]:
        if self._pattern.match(request.uri.path):
            return Ok(self._nj)
        return Ok(None)
