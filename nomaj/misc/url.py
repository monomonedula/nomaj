import re
from typing import TypeVar, Generic, Callable, Mapping, Optional
from urllib.parse import ParseResult

from koda import Ok, Result, Err


def href(p: ParseResult) -> str:
    """
    Extract path and query from url
    """
    if p.query:
        return f"{p.path}?{p.query}"
    return p.path


class Regex:
    _ttable: Mapping[str, str] = {
        "int": r"\d+",
        "str": r"[^/]+",
        "slug": r"[\w-]+",
        "uuid": r"[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}",
        "path": r".+",
    }

    def __init__(self, ttable: Optional[Mapping[str, str]] = None):
        if ttable:
            self._ttable = ttable

    def __call__(self, segment: str) -> str:
        if segment.startswith("{"):
            if ":" in segment:
                _, typ = segment.split(":")
            else:
                typ = "str"
            return self._ttable[typ]
        else:
            return segment

    @classmethod
    def with_(cls, ttable: Mapping[str, str]):
        return cls(
            {
                **cls._ttable,
                **ttable,
            }
        )


_T = TypeVar("_T")


class Path:
    def __init__(
        self,
        p: str,
        trailing_slash_optional: bool = False,
        prefix: bool = False,
        path_converter: Regex = Regex(),
    ):
        self._p: str = "/" + p.strip("/") + "/" if p.strip("/") else "/"
        self._trailing_slash_optional = trailing_slash_optional
        self._pattern = re.compile(
            "^/"
            + "/".join(
                [
                    path_converter(segment.strip("{}"))
                    for segment in p.split("/")
                    if segment
                ]
            )
            + ("/?" if trailing_slash_optional else "/")
            + ("" if prefix else "$")
        )
        self.params = tuple(
            [name.strip("{}") for name in p.split("/") if name.startswith("{")]
        )

    def matches(self, p: str):
        return bool(self._pattern.match(p))

    def with_postfix(self, sp: str, trailing_slash_optional: bool = False) -> "Path":
        return Path(self._p + sp.strip("/"), trailing_slash_optional)

    def path_params_of(self, p: str) -> Result[Mapping[str, str], Exception]:
        if not self.matches(p):
            return Err(
                ValueError(f"Cannot extract path params of {self._p!r} from {p!r}")
            )
        return Ok(
            {
                name: value
                for name, value in zip(self.params, self._pattern.findall(p.strip("/")))
            }
        )

    def __str__(self):
        return f"{self.__class__.__name__}[{self._p}, {self._pattern}]"

    def as_prefix(self):
        return Path(self._p, self._trailing_slash_optional, prefix=True)


class PathParam(Generic[_T]):
    def __init__(self, name: str, as_type: Callable[[str], _T]):
        self._name: str = name
        self._as_type: Callable[[str], _T] = as_type

    def extract(self, params: Mapping[str, str]) -> Result[_T, Exception]:
        val = params.get(self._name)
        if val is None:
            return Err(ValueError(f"Missing parameter {val!r} in {params}"))
        return Ok(self._as_type(val))

    def name(self):
        return self._name
