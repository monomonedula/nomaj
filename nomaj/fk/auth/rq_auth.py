import dataclasses
from typing import Optional, Union
from dataclasses import replace

from koda import Result, Ok, Err

from nomaj.fk.auth.codecs.cc_plain import CcPlain
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.nj_auth import NjAuth
from nomaj.nomaj import Req
from nomaj.rq.rq_with_headers import rq_with_headers


@dataclasses.dataclass(frozen=True)
class RqAuth(Req):
    identity: Identity


def rq_authenticated(
    rq: Req, header: str = NjAuth.__name__
) -> Result[RqAuth, Exception]:
    val: Optional[str] = rq.headers.getone(header, None)
    if val is None:
        identity = ANONYMOUS
    else:
        result = CcPlain().decode(val.encode())
        if isinstance(result, Err):
            return result
        identity = result.val
    return Ok(
        RqAuth(
            uri=rq.uri,
            headers=rq.headers,
            method=rq.method,
            body=rq.body,
            identity=identity,
        )
    )


def rq_with_auth(rq: Req, identity: Union[str, Identity], header: str) -> Req:
    encoded = CcPlain().encode(
        Identity(urn=identity) if isinstance(identity, str) else identity
    )
    return rq_with_headers(rq, [(header, encoded.decode())])
