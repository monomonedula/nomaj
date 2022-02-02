import base64
import dataclasses
import json
from abc import abstractmethod, ABC
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import List, Optional, Mapping, Any, Tuple


from nvelope import Obj, string_conv, float_conv, int_conv, ConversionOf

from nomaj.fk.auth.codecs.codec import Codec
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.signature import Signature
from nomaj.maybe import Maybe, Just, Err, Caught
from nomaj.misc.cookies import cookies_of
from nomaj.misc.expires import Date
from nomaj.nomaj import Req, Resp
from nomaj.rs.rs_with_cookie import rs_with_cookie



class Pass(ABC):
    """
    Pass to enter a user and let him exit.

    This interface is intended for authentication handling.
    """

    @abstractmethod
    async def enter(self, request: Req) -> Maybe[Identity]:
        """
        Authenticate the user by the request.
        """
        pass

    @abstractmethod
    async def exit(self, response: Resp, identity: Identity) -> Maybe[Resp]:
        """
        Maybe put some authentication credentials into the response.
        """
        pass


class PsAll(Pass):
    def __init__(self, passes: List[Pass], identity: int):
        if identity not in range(len(passes)):
            raise ValueError(
                f"Bad identity index ({identity}) for a list of {len(passes)} passes"
            )
        self._passes: List[Pass] = passes
        self._index: int = identity

    async def enter(self, request: Req) -> Maybe[Identity]:
        identities: List[Maybe[Identity]] = []
        for p in self._passes:
            identity: Maybe[Identity] = await p.enter(request)
            if identity.err() or identity.value() == ANONYMOUS:
                return identity
            identities.append(identity)
        return identities[self._index]

    async def exit(self, response: Resp, identity: Identity) -> Maybe[Resp]:
        return await self._passes[self._index].exit(response, identity)


class PsLogout(Pass):
    async def enter(self, request: Req) -> Maybe[Identity]:
        return Just(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Maybe[Resp]:
        return Just(response)


class PsCookie(Pass):
    """
    Pass via cookie information.

    :param codec: a codec to encode identities.
    :param name: cookie name. Default to `PsCookie`.
    :param days: cookie expiration time in days. Default to 30 days
    """

    def __init__(self, codec: Codec, name: Optional[str] = None, days: int = 30):
        self._codec: Codec = codec
        self._name: str = (name or self.__class__.__name__).strip()
        self._days: int = days

    async def enter(self, request: Req) -> Maybe[Identity]:
        value: Optional[str] = cookies_of(request).get(self._name)
        if value is not None:
            return self._codec.decode(value)
        return ANONYMOUS

    async def exit(self, response: Resp, identity: Identity) -> Maybe[Resp]:
        """
        Adds authentication cookie to the response
        """
        if identity == ANONYMOUS:
            text = ""
        else:
            text = self._codec.encode(identity)
        return Just(
            rs_with_cookie(
                response,
                self._name,
                text,
                "Path=/",
                "HttpOnly",
                await Date(
                    datetime.utcnow() + timedelta(days=self._days),
                ).print(),
            )
        )


class PsChain(Pass):
    def __init__(self, passes: List[Pass]):
        self._passes: List[Pass] = passes

    async def enter(self, request: Req) -> Maybe[Identity]:
        for p in self._passes:
            identity: Maybe[Identity] = await p.enter(request)
            if identity.err() or identity.value() != ANONYMOUS:
                return identity
        return Just(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Maybe[Resp]:
        r = Just(response)
        for p in self._passes:
            r = await p.exit(r.value(), identity)
            if r.err():
                break
        return r


class PsFixed(Pass):
    def __init__(self, idt: Identity):
        self._idt: Maybe[Identity] = Just(idt)

    async def enter(self, request: Req) -> Maybe[Identity]:
        return self._idt

    async def exit(self, response: Resp, identity: Identity) -> Maybe[Resp]:
        return Just(response)


dt_conv = ConversionOf(
    to_json=lambda dt: dt.timestamp(),
    from_json=lambda tstamp: datetime.fromtimestamp(tstamp)
)


@dataclasses.dataclass(frozen=True)
class JwtHeader(Obj):
    _conversion = {
        "alg": string_conv,
        "typ": string_conv,
    }

    alg: str
    typ: str = "JWT"


@dataclasses.dataclass(frozen=True)
class JwtPayload(Obj):
    _conversion = {
        "iat": dt_conv,
        "exp": dt_conv,
        "sub": string_conv,
        "dest": string_conv,
    }
    iat: datetime
    exp: datetime
    sub: str
    dest: str = ""


@dataclasses.dataclass(frozen=True)
class JwtProto(Obj):
    header: JwtHeader
    payload: JwtPayload


@dataclasses.dataclass(frozen=True)
class Jwt:
    header: JwtHeader
    payload: JwtPayload
    encoded: bytes


class Validation(ABC):
    @abstractmethod
    def passes_for(self, token: Jwt) -> Tuple[bool, str]:
        pass


class JwtEntry:
    def __init__(
        self,
        signature: Signature,
        validation: Validation,
        age: int = 86400,
    ):
        self._signature: Signature = signature
        self._age: int = age
        self._validation: Validation = validation

    def new_token(self, idt: Identity, iat: datetime) -> Jwt:
        header = JwtHeader(
            alg=self._signature.name(),
            typ="JWT"
        )
        payload = JwtPayload(
            iat=iat,
            exp=iat + timedelta(seconds=self._age),
            sub=idt.urn,
        )
        return Jwt(
            header,
            payload,
            encoded=encoded_token(self._signature, header, payload)
        )

    def enter(self, raw_token: str) -> Maybe[Identity]:
        try:
            header, payload, signature_bytes = raw_token.split(".")
        except ValueError as e:
            return Err(Caught(e, "JWT format error"))
        try:
            token = Jwt(
                JwtHeader.from_json(json.loads(base64.urlsafe_b64decode(header))),
                JwtPayload.from_json(json.loads(base64.urlsafe_b64decode(payload))),
                raw_token.encode(),
            )
        except json.JSONDecodeError as e:
            return Err(Caught(e, "JWT JSON decoding error"))
        if encoded_token(self._signature, token.header, token.payload) == raw_token:
            valid, info = self._validation.passes_for(token)
            if valid:
                return Just(Identity(token.payload.sub))
        return Just(ANONYMOUS)


class PsTokenAccess(Pass):
    def __init__(self, entry: JwtEntry, header: str = "Authorization"):
        self._entry: JwtEntry = entry
        self._header: str = header

    async def enter(self, request: Req) -> Maybe[Identity]:
        for v in request.headers.getall(self._header):
            if v.strip().startswith("Bearer"):
                return self._entry.enter(
                    v.split("Bearer")[1].strip()
                )
        return Just(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Maybe[Resp]:
        return Just(response)


def encoded_token(s: Signature, jwt_header: JwtHeader, jwt_payload: JwtPayload) -> bytes:
    header: bytes = base64.urlsafe_b64encode(
        json.dumps(jwt_header.as_json(), sort_keys=True).encode()
    )
    payload: bytes = base64.urlsafe_b64encode(
        json.dumps(jwt_payload.as_json(), sort_keys=True).encode()
    )
    data: bytes = b".".join((header, payload))
    signature = base64.urlsafe_b64encode(s.sign(data))
    return b".".join((data, signature))
