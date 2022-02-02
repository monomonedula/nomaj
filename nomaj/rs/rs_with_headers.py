from dataclasses import replace
from typing import Tuple, Collection

from multidict import CIMultiDictProxy, CIMultiDict

from nomaj.nomaj import Resp


def rs_with_headers(rs: Resp, headers: Collection[Tuple[str, str]]) -> Resp:
    new_headers: CIMultiDict[str] = CIMultiDict(rs.headers)
    for h, v in headers:
        new_headers.add(h, v)
    return replace(rs, headers=CIMultiDictProxy(new_headers))
