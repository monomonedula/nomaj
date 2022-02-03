import base64
import dataclasses
import json
from abc import abstractmethod, ABC
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union, AsyncIterable
from urllib.parse import ParseResult

from nvelope import Obj, string_conv, datetime_timestamp_conv, NvelopeError

from nomaj.fk.auth.codecs.codec import Codec
from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.signature import Signature
from nomaj.http.app_basic import BodyFromIterable, BodyOf
from nomaj.failable import Failable, Just, Err, Caught
from nomaj.misc.cookies import cookies_of
from nomaj.misc.expires import Date
from nomaj.nomaj import Req, Resp, Body
from nomaj.rs.rs_with_cookie import rs_with_cookie
from nomaj.rs.rs_with_headers import rs_with_headers
from nomaj.rs.rs_without_headers import rs_without_headers


class Pass(ABC):
    """
    Pass to enter a user and let him exit.

    This interface is intended for authentication handling.
    """

    @abstractmethod
    async def enter(self, request: Req) -> Failable[Identity]:
        """
        Authenticate the user by the request.
        """
        pass

    @abstractmethod
    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        """
        Failable put some authentication credentials into the response.
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

    async def enter(self, request: Req) -> Failable[Identity]:
        identities: List[Failable[Identity]] = []
        for p in self._passes:
            identity: Failable[Identity] = await p.enter(request)
            if identity.err() or identity.value() == ANONYMOUS:
                return identity
            identities.append(identity)
        return identities[self._index]

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        return await self._passes[self._index].exit(response, identity)


class PsLogout(Pass):
    async def enter(self, request: Req) -> Failable[Identity]:
        return Just(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
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

    async def enter(self, request: Req) -> Failable[Identity]:
        value: Optional[str] = cookies_of(request).get(self._name)
        if value is not None:
            return self._codec.decode(value)
        return ANONYMOUS

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
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

    async def enter(self, request: Req) -> Failable[Identity]:
        for p in self._passes:
            identity: Failable[Identity] = await p.enter(request)
            if identity.err() or identity.value() != ANONYMOUS:
                return identity
        return Just(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        r = Just(response)
        for p in self._passes:
            r = await p.exit(r.value(), identity)
            if r.err():
                break
        return r


class PsFixed(Pass):
    def __init__(self, idt: Identity):
        self._idt: Failable[Identity] = Just(idt)

    async def enter(self, request: Req) -> Failable[Identity]:
        return self._idt

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        return Just(response)


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
    _keep_undefined = True

    _conversion = {
        "iat": datetime_timestamp_conv,
        "exp": datetime_timestamp_conv,
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
    encoded: str


class Validation(ABC):
    @abstractmethod
    async def verdict_for(self, token: Jwt) -> Tuple[bool, str]:
        pass


class VdIsAccessToken(Validation):
    async def verdict_for(self, token: Jwt) -> Tuple[bool, str]:
        if token.payload.dest == "access":
            return True, ""
        return False, "not access token"


class VdIsRefreshToken(Validation):
    async def verdict_for(self, token: Jwt) -> Tuple[bool, str]:
        if token.payload.dest == "refresh":
            return True, ""
        return False, "not refresh token"


class VdSignature(Validation):
    def __init__(self, sign: Signature):
        self._signature: Signature = sign

    async def verdict_for(self, token: Jwt) -> Tuple[bool, str]:
        if token_b64(self._signature, token.header, token.payload) == token.encoded:
            return True, ""
        return False, "token signature mismatch"


class VdExpiration(Validation):
    async def verdict_for(self, token: Jwt) -> Tuple[bool, str]:
        if token.payload.exp < datetime.utcnow():
            return False, "token expired"
        return True, ""


class VdSequence(Validation):
    def __init__(self, *vds: Validation):
        self._vds: Tuple[Validation, ...] = vds

    async def verdict_for(self, token: Jwt) -> Tuple[bool, str]:
        for vd in self._vds:
            valid, info = await vd.verdict_for(token)
            if not valid:
                return valid, info
        return True, ""


class JwtEntry(ABC):
    @abstractmethod
    def new_token(self, idt: Identity, iat: datetime) -> Jwt:
        pass

    @abstractmethod
    def enter(self, raw_token: str) -> Failable[Identity]:
        pass


class JwtEntrySimple:
    def __init__(
        self,
        signature: Signature,
        validation: Optional[Validation] = None,
        age: int = 86400,
    ):
        self._signature: Signature = signature
        self._age: int = age
        self._validation: Validation = VdSequence(
            VdSignature(signature),
            VdExpiration(),
            *([validation] if validation else []),
        )

    def new_token(self, idt: Identity, iat: datetime) -> Jwt:
        header = JwtHeader(alg=self._signature.name(), typ="JWT")
        payload = JwtPayload(
            iat=iat,
            exp=iat + timedelta(seconds=self._age),
            sub=idt.urn,
        )
        return Jwt(header, payload, encoded=token_b64(self._signature, header, payload))

    async def enter(self, raw_token: str) -> Failable[Identity]:
        try:
            header, payload, signature_bytes = raw_token.split(".")
        except ValueError as e:
            return Err(Caught(e, "JWT format error"))
        try:
            token = Jwt(
                JwtHeader.from_json(json.loads(base64.urlsafe_b64decode(header))),
                JwtPayload.from_json(json.loads(base64.urlsafe_b64decode(payload))),
                raw_token,
            )
        except (json.JSONDecodeError, NvelopeError) as e:
            return Err(Caught(e, "JWT JSON parsing error"))
        valid, info = await self._validation.verdict_for(token)
        return Just(
            Identity(token.payload.sub, {"from_token": raw_token})
            if valid
            else ANONYMOUS
        )


class JwtEntryAccess(JwtEntrySimple):
    def __init__(
        self,
        signature: Signature,
        validation: Optional[Validation] = None,
        age: int = 86400,
    ):
        super(JwtEntryAccess, self).__init__(
            signature,
            VdSequence(
                VdIsAccessToken(),
                validation,
            )
            if validation
            else VdIsAccessToken(),
            age,
        )


class JwtEntryRefresh(JwtEntrySimple):
    def __init__(
        self,
        signature: Signature,
        validation: Optional[Validation] = None,
        age: int = 86400,
    ):
        super(JwtEntryRefresh, self).__init__(
            signature,
            VdSequence(
                VdIsRefreshToken(),
                validation,
            )
            if validation
            else VdIsRefreshToken(),
            age,
        )


class PsToken(Pass):
    def __init__(self, entry: JwtEntry, header: str = "Authorization"):
        self._entry: JwtEntry = entry
        self._header: str = header

    async def enter(self, request: Req) -> Failable[Identity]:
        for v in request.headers.getall(self._header):
            if v.strip().startswith("Bearer"):
                return self._entry.enter(v.split("Bearer")[1].strip())
        return Just(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        token = self._entry.new_token(identity, iat=datetime.utcnow())
        return Just(rs_json(rs_with_body(response, json.dumps({"jwt": token.encoded}))))


def rs_with_body(
    resp: Resp, body: Union[Body, str, bytes, AsyncIterable[bytes]]
) -> Resp:
    new_body: Body
    if isinstance(body, (str, bytes)):
        new_body = BodyOf(body)
    elif isinstance(body, Body):
        new_body = body
    else:
        new_body = BodyFromIterable(body.__aiter__())
    return dataclasses.replace(resp, body=new_body)


def rs_json(resp: Resp) -> Resp:
    return rs_with_type(resp, "application/json")


def rs_with_type(resp: Resp, content_type: str, charset: Optional[str] = None) -> Resp:
    return rs_with_headers(
        rs_without_headers(
            resp,
            ("Content-Type",),
        ),
        (("Content-Type", content_type),)
        if charset is None
        else (("Content-Type", f"{content_type}; charset={charset}"),),
    )


def token_b64(s: Signature, jwt_header: JwtHeader, jwt_payload: JwtPayload) -> str:
    header: bytes = base64.urlsafe_b64encode(
        json.dumps(jwt_header.as_json(), sort_keys=True).encode()
    )
    payload: bytes = base64.urlsafe_b64encode(
        json.dumps(jwt_payload.as_json(), sort_keys=True).encode()
    )
    data: bytes = b".".join((header, payload))
    signature = base64.urlsafe_b64encode(s.sign(data))
    return b".".join((data, signature)).decode()


def href(p: ParseResult) -> str:
    """
    Extract path and query from url
    """
    if p.query:
        return f"{p.path}?{p.query}"
    return p.path


class Entry(ABC):
    @abstractmethod
    async def enter(self, user: str, password: str) -> Failable[Identity]:
        pass


class PsBasic(Pass):
    def __init__(self, realm: str, basic: Entry):
        self._realm: str = realm
        self._entry: Entry = basic

    async def enter(self, request: Req) -> Failable[Identity]:
        if (
            "authorization" not in request.headers
            or "Basic" not in request.headers["authorization"]
        ):
            identity = ANONYMOUS
        else:
            auth: str = base64.b64decode(
                request.headers["authorization"].split("Basic")[1].strip()
            ).decode()
            user, password = auth.split(":", maxsplit=1)
            identity: Failable[Identity] = await self._entry.enter(user, password)
        return identity

    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        return Just(response)
