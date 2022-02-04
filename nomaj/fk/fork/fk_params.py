import re
from typing import Union, Pattern, Optional
from urllib.parse import parse_qsl

from nomaj.failable import Failable, Ok
from nomaj.fork import Fork
from nomaj.nj.nj_fixed import NjFixed
from nomaj.nomaj import Nomaj, Resp, Req
from nomaj.rs.rs_text import rs_text


class FkParams(Fork):
    """
    Fork by query params and their values, matched by regular expression.
    This class is immutable and thread safe.
    """
    def __init__(
        self,
        param: str,
        pattern: Union[str, Pattern],
        resp: Union[Nomaj, Resp, str],
    ):
        self._param: str = param
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
        for param, value in parse_qsl(request.uri.query):
            if param == self._param and self._pattern.match(value):
                return Ok(self._nj)
        return Ok(None)
