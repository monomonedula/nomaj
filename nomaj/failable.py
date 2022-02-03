from abc import abstractmethod
from typing import TypeVar, Generic, Optional, cast, Any, Dict

T = TypeVar("T")


class Failable(Generic[T]):
    @abstractmethod
    def value(self) -> T:
        pass

    @abstractmethod
    def err(self) -> Optional[Exception]:
        pass


class Ok(Failable[T]):
    __slots__ = ("_v",)

    def __init__(self, v: T):
        self._v: T = v

    def value(self) -> T:
        return self._v

    def err(self) -> Optional[Exception]:
        return None


class Err(Failable[T]):
    __slots__ = ("_err",)

    def __init__(self, err: Exception):
        self._err: Exception = err

    def value(self) -> T:
        raise self._err

    def err(self) -> Optional[Exception]:
        return self._err


X = TypeVar("X")
Y = TypeVar("Y")


def err_(e: Failable[X]) -> Err[Y]:
    assert e.err()
    return cast(Err[Y], e)


class Caught(Exception):
    def __init__(self, e: Exception, info: str, ctx: Optional[Dict[str, Any]] = None):
        self.e: Exception = e
        self.info: str = info
        self.ctx: Optional[Dict[str, Any]] = ctx
