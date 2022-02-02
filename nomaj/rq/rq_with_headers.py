from dataclasses import replace
from typing import Tuple, Collection

from multidict import CIMultiDictProxy, CIMultiDict

from nomaj.nomaj import Req


def rq_with_headers(rq: Req, headers: Collection[Tuple[str, str]]) -> Req:
    new_headers: CIMultiDict[str] = CIMultiDict(rq.headers)
    for h, v in headers:
        new_headers.add(h, v)
    return replace(rq, headers=CIMultiDictProxy(new_headers))
