from typing import Optional

from nomaj.nomaj import Resp
from nomaj.rs.rs_with_headers import rs_with_headers
from nomaj.rs.rs_without_headers import rs_without_headers


def rs_with_type(resp: Resp, content_type: str, charset: Optional[str] = None) -> Resp:
    return rs_with_headers(
        rs_without_headers(
            resp,
            ("Content-Type",),
        ),
        (("Content-Type", content_type),)
        if charset is None
        else (("Content-Type", f"{content_type}; charset={charset}"),),
    )


def rs_json(resp: Resp) -> Resp:
    return rs_with_type(resp, "application/json")
