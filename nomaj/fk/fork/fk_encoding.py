from itertools import chain
from typing import Optional, Union, List

from werkzeug.http import parse_accept_header

from nomaj.failable import Failable, Ok
from nomaj.fork import Fork
from nomaj.nj.nj_fixed import NjFixed
from nomaj.nomaj import Nomaj, Resp, Req


class FkEncoding(Fork):
    def __init__(self, encoding: str, resp: Union[Resp, Nomaj]):
        self._nj: Nomaj = NjFixed(resp) if isinstance(resp, Resp) else resp
        self._encoding: str = encoding.strip()

    def route(self, request: Req) -> Failable[Optional[Nomaj]]:
        headers: Optional[List[str]] = request.headers.getall("accept-encoding")
        if (
            not headers
            or not self._encoding
            or self._encoding
            in [
                enc
                for enc, priority in chain.from_iterable(
                    parse_accept_header(val) for val in headers
                )
            ]
        ):
            return Ok(self._nj)
        return Ok(None)
