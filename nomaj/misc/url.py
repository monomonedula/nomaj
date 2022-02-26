import dataclasses
import re
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Callable, Mapping, Optional, Dict, Tuple
from urllib.parse import ParseResult

from koda import Ok, Result, Err
from nvelope import JSON


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
                _, typ = segment.strip("{}").split(":")
            else:
                typ = "str"
            return f"({self._ttable[typ]})"
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


class Path(ABC):
    @abstractmethod
    def path_params_of(self, p: str) -> Result[Mapping[str, str], Exception]:
        pass

    @abstractmethod
    def matches(self, p: str) -> bool:
        pass

    @abstractmethod
    def raw(self) -> str:
        pass

    @abstractmethod
    def meta(self) -> Dict[str, JSON]:
        pass

    @abstractmethod
    def params(self) -> Tuple[str, ...]:
        pass

    @abstractmethod
    def param_names(self) -> Tuple[str, ...]:
        pass


@dataclasses.dataclass
class ParamMeta:
    schema: Dict[str, JSON]
    description: str


class PathSimple(Path):
    def __init__(
        self,
        p: str,
        trailing_slash_optional: bool = False,
        prefix: bool = False,
        regex: Regex = Regex(),
    ):
        self._p: str = "/" + p.strip("/") + "/" if p.strip("/") else "/"
        self._trailing_slash_optional = trailing_slash_optional
        self._pattern = re.compile(
            "^/"
            + "/".join([regex(segment) for segment in p.split("/") if segment])
            + ("/?" if trailing_slash_optional else "/")
            + ("" if prefix else "$")
        )
        self._params = tuple(
            [name.strip("{}") for name in p.split("/") if name.startswith("{")]
        )
        self._param_names = tuple([p.split(":")[0] for p in self._params])

    def params(self) -> Tuple[str, ...]:
        return self._params

    def param_names(self) -> Tuple[str, ...]:
        return self._param_names

    def matches(self, p: str) -> bool:
        return bool(self._pattern.match(p))

    def with_postfix(
        self,
        sp: str,
        trailing_slash_optional: bool = False,
    ) -> "PathSimple":
        return PathSimple(
            self._p + sp.strip("/"), trailing_slash_optional=trailing_slash_optional
        )

    def path_params_of(self, p: str) -> Result[Mapping[str, str], Exception]:
        if not self.matches(p):
            return Err(
                ValueError(f"Cannot extract path params of {self._p!r} from {p!r}")
            )
        return Ok(
            {
                name: value
                for name, value in zip(self.param_names(), self._pattern.findall(p))
            }
        )

    def __str__(self):
        return f"{self.__class__.__name__}[{self._p}, {self._pattern}]"

    def as_prefix(self) -> "PathSimple":
        return PathSimple(self._p, self._trailing_slash_optional, prefix=True)

    def as_end(self) -> "PathSimple":
        return PathSimple(self._p, self._trailing_slash_optional, prefix=False)

    def raw(self) -> str:
        return self._p

    def meta(self) -> Dict[str, JSON]:
        arr = []
        for param in self.params():
            name, typ = param.split(":")
            info = ParamMeta(
                {
                    "int": {"type": "integer"},
                    "str": {"type": "string"},
                    "slug": {"type": "string"},
                    "uuid": {"type": "string"},
                    "path": {"type": "string"},
                }.get(typ, "string"),
                "",
            )
            arr.append(
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "description": info.description,
                    "schema": info.schema,
                }
            )

        return {
            "parameters": arr,
            "path": path_to_swagger(self.raw()),
        }


class PathParam(Generic[_T]):
    def __init__(self, name: str, as_type: Callable[[str], _T]):
        self._name: str = name
        self._as_type: Callable[[str], _T] = as_type

    def extract(self, params: Mapping[str, str]) -> Result[_T, Exception]:
        val = params.get(self._name)
        if val is None:
            return Err(
                ValueError(f"Missing parameter {self._name!r} in path params {params}")
            )
        return Ok(self._as_type(val))

    def name(self):
        return self._name


def path_to_swagger(p: str) -> str:
    if p.strip("/"):
        return (
            "/"
            + "/".join(
                [
                    "{" + part.strip("{}").split(":")[0] + "}"
                    if part.startswith("{")
                    else part
                    for part in p.split("/")
                    if part
                ]
            )
            + "/"
        )
    return "/"
