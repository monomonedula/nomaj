from dataclasses import replace
from typing import Collection

from multidict import CIMultiDict, CIMultiDictProxy

from nomaj.nomaj import Resp


def rs_without_headers(rs: Resp, removed_headers: Collection[str]) -> Resp:
    new_headers: CIMultiDict[str] = CIMultiDict(rs.headers)
    for h in removed_headers:
        if h in new_headers:
            del new_headers[h]
    return replace(rs, headers=CIMultiDictProxy(new_headers))
