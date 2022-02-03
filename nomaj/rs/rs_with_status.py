from dataclasses import replace
from typing import Optional

from nomaj.nomaj import Resp
from nomaj.rs.rs_empty import rs_empty


def rs_with_status(status: int, resp: Optional[Resp]) -> Resp:
    assert status in range(100, 1000)
    return replace(resp or rs_empty(), status=status)
