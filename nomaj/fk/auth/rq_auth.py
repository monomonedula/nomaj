from typing import Optional, Union
from dataclasses import replace

from nomaj.fk.auth.codecs.cc_plain import CcPlain
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.nm_auth import NmAuth
from nomaj.maybe import Maybe, Just, err_
from nomaj.nomaj import Req
from nomaj.rq.rq_with_headers import rq_with_headers


class RqAuth(Req):
    identity: Identity


def rq_authenticated(rq: Req, header: str = NmAuth.__name__) -> Maybe[RqAuth]:
    val: Optional[str] = rq.headers.getone(header, None)
    if val is None:
        identity = Just(ANONYMOUS)
    else:
        identity = CcPlain().decode(val)
        if identity.err() is not None:
            return err_(identity)
    return replace(
        **rq.__dict__,
        identity=identity,
    )


def rq_with_auth(rq: Req, identity: Union[str, Identity], header: str) -> Req:
    encoded = CcPlain().encode(
        Identity(urn=identity) if isinstance(identity, str) else identity
    )
    return rq_with_headers(rq, [(header, encoded)])
