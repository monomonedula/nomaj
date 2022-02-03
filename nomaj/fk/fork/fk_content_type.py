from typing import Optional, Union, Collection

from werkzeug.datastructures import MIMEAccept
from werkzeug.http import parse_accept_header

from nomaj.failable import Failable, Ok
from nomaj.fork import Fork
from nomaj.nj.nj_fixed import NjFixed
from nomaj.nomaj import Nomaj, Resp, Req


class FkContentType(Fork):
    def __init__(self, types: Collection[str], resp: Union[Resp, Nomaj]):
        self._nj: Nomaj = NjFixed(resp) if isinstance(resp, Resp) else resp
        self._ctypes: Collection[str] = types

    def route(self, request: Req) -> Failable[Optional[Nomaj]]:
        if request.headers.get("Content-Type"):
            if parse_accept_header(
                request.headers.get("Content-Type", "*/*"), MIMEAccept
            ).best_match(self._ctypes):
                return Ok(self._nj)
        else:
            if "*/*" in self._ctypes:
                return Ok(self._nj)
        return Ok(None)
