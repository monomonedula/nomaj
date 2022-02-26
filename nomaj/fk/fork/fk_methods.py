from typing import Tuple, Union, Optional, Dict

from koda import Result, Ok
from nvelope import JSON

from nomaj.fork import Fork
from nomaj.nj.nj_fixed import NjFixed
from nomaj.nomaj import Nomaj, Resp, Req


class FkMethods(Fork):
    def __init__(self, *methods: str, resp: Union[Nomaj, Resp]):
        self._methods: Tuple[str, ...] = methods
        self._nj: Nomaj
        if isinstance(resp, Resp):
            self._nj = NjFixed(resp)
        elif isinstance(resp, Nomaj):
            self._nj = resp
        else:
            raise TypeError("Expected Response, Nomaj or str. Got: %r" % type(resp))

    def route(self, request: Req) -> Result[Optional[Nomaj], Exception]:
        if request.method in self._methods:
            return Ok(self._nj)
        return Ok(None)

    def meta(self) -> Dict[str, JSON]:
        return {
            "fork": {
                "type": self.__class__.__name__,
                "methods": list(self._methods),
            },
            "children": [self._nj.meta()],
        }
