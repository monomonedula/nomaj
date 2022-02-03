from multidict import CIMultiDictProxy, CIMultiDict

from nomaj.body import EmptyBody
from nomaj.nomaj import Resp


def rs_empty() -> Resp:
    return Resp(
        204,
        CIMultiDictProxy(CIMultiDict()),
        EmptyBody(),
    )
