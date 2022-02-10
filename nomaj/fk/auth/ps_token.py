import base64
import dataclasses
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Tuple, Optional

from nvelope import Obj, string_conv, datetime_timestamp_conv, NvelopeError
from koda import Result, Err, Ok

from nomaj.fk.auth.identity import Identity, ANONYMOUS
from nomaj.fk.auth.ps import Pass
from nomaj.result import Caught
from nomaj.rs.rs_with_body import rs_with_body
from nomaj.rs.rs_with_type import rs_json
from nomaj.fk.auth.signature import Signature
from nomaj.nomaj import Req, Resp


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
    def enter(self, raw_token: str) -> Result[Identity, Exception]:
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

    async def enter(self, raw_token: str) -> Result[Identity, Exception]:
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
        return Ok(
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

    async def enter(self, request: Req) -> Result[Identity, Exception]:
        for v in request.headers.getall(self._header):
            if v.strip().startswith("Bearer"):
                return self._entry.enter(v.split("Bearer")[1].strip())
        return Ok(ANONYMOUS)

    async def exit(self, response: Resp, identity: Identity) -> Result[Resp, Exception]:
        token = self._entry.new_token(identity, iat=datetime.utcnow())
        return Ok(rs_json(rs_with_body(response, json.dumps({"jwt": token.encoded}))))


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
