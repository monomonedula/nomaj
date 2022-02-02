from types import MappingProxyType
from typing import Mapping

from nomaj.nomaj import Req


def cookies_of(request: Req) -> Mapping[str, str]:
    cookies_map = {}
    for cookies in request.headers.getall("cookie", []):
        name: str
        value: str
        for cookie in cookies.split(";"):
            if cookie.strip():
                name, value = cookie.strip().split("=")
                cookies_map[name.strip()] = value.strip()
    return MappingProxyType(cookies_map)
