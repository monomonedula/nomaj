import re
from typing import Union, Pattern, Optional, Dict
from urllib.parse import parse_qsl

from koda import Result, Ok
from nvelope import JSON

from nomaj.fork import Fork
from nomaj.nj.nj_fixed import NjFixed
from nomaj.nomaj import Nomaj, Resp, Req
from nomaj.rs.rs_text import rs_text


class FkParams(Fork):
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

    def route(self, request: Req) -> Result[Optional[Nomaj], Exception]:
        for param, value in parse_qsl(request.uri.query):
            if param == self._param and self._pattern.match(value):
                return Ok(self._nj)
        return Ok(None)

    def meta(self) -> Dict[str, JSON]:
        return {
            "fork": {
                "type": self.__class__.__name__,
                "param": self._param,
                "param_pattern": self._pattern.pattern,
            },
            "children": [self._nj.meta()],
        }
