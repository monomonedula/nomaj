import dataclasses
from typing import Union, AsyncIterable

from nomaj.body import BodyOf, Body, BodyFromIterable
from nomaj.nomaj import Resp


def rs_with_body(
    resp: Resp, body: Union[Body, str, bytes, AsyncIterable[bytes]]
) -> Resp:
    new_body: Body
    if isinstance(body, (str, bytes)):
        new_body = BodyOf(body)
    elif isinstance(body, Body):
        new_body = body
    else:
        new_body = BodyFromIterable(body.__aiter__())
    return dataclasses.replace(resp, body=new_body)
