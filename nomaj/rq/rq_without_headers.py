from dataclasses import replace
from typing import Collection

from multidict import CIMultiDict, CIMultiDictProxy

from nomaj.nomaj import Req


def rq_without_headers(rq: Req, removed_headers: Collection[str]) -> Req:
    new_headers: CIMultiDict[str] = CIMultiDict(rq.headers)
    for h in removed_headers:
        if h in new_headers:
            del new_headers[h]
    return replace(rq, headers=CIMultiDictProxy(new_headers))
