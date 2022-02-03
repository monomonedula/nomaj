from typing import Optional, Union
from dataclasses import replace

from nomaj.fk.auth.codecs.cc_plain import CcPlain
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.nj_auth import NjAuth
from nomaj.failable import Failable, Ok, err_
from nomaj.nomaj import Req
from nomaj.rq.rq_with_headers import rq_with_headers


class RqAuth(Req):
    identity: Identity


def rq_authenticated(rq: Req, header: str = NjAuth.__name__) -> Failable[RqAuth]:
    val: Optional[str] = rq.headers.getone(header, None)
    if val is None:
        identity = ANONYMOUS
    else:
        failable_identity = CcPlain().decode(val.encode())
        if failable_identity.err() is not None:
            return err_(failable_identity)
        identity = failable_identity.value()
    return Ok(
        replace(
            **rq.__dict__,
            identity=identity,
        )
    )


def rq_with_auth(rq: Req, identity: Union[str, Identity], header: str) -> Req:
    encoded = CcPlain().encode(
        Identity(urn=identity) if isinstance(identity, str) else identity
    )
    return rq_with_headers(rq, [(header, encoded.decode())])
