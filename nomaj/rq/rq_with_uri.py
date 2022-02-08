from dataclasses import replace
from urllib.parse import ParseResult

from nomaj.nomaj import Req


def rq_with_path(rq: Req, p: str) -> Req:
    return replace(rq, uri=rq.uri._replace(path=p))


def rq_with_uri(rq: Req, uri: ParseResult) -> Req:
    return replace(rq, uri=uri)
