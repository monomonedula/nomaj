from typing import Union, Pattern

from nomaj.fk.fork.fk_regex import FkRegex
from nomaj.fk.fork.nj_fork import NjFork
from nomaj.nomaj import Nomaj, Resp


def nj_regex(pattern: Union[str, Pattern], *, resp: Union[Nomaj, Resp, str]) -> Nomaj:
    return NjFork(FkRegex(pattern, resp=resp))
