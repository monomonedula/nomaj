from nomaj.nomaj import Resp
from nomaj.rs.rs_with_headers import rs_with_headers


def rs_with_cookie(rs: Resp, name: str, value: str, *attrs: str) -> Resp:
    base: str = f"{name}={value};"
    attributes: str = ";".join(attrs) + ";"
    return rs_with_headers(rs, [("Set-Cookie", f"{base}{attributes}")])
