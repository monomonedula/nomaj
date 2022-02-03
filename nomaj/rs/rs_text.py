from typing import Union, Optional

from multidict import CIMultiDictProxy, CIMultiDict

from nomaj.body import BodyOf
from nomaj.nomaj import Resp
from nomaj.rs.rs_with_body import rs_with_body
from nomaj.rs.rs_with_type import rs_with_type


def rs_text(text: Union[str, bytes] = "", response: Optional[Resp] = None) -> Resp:
    if response is None:
        response = Resp(200, CIMultiDictProxy(CIMultiDict()), BodyOf(text))
    if text:
        response = rs_with_body(response, text)
    return rs_with_type(response, "text/plain")
