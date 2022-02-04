import json
from dataclasses import replace

from nvelope import JSON, Compound, NvelopeError

from nomaj.failable import Failable, Ok, Err
from nomaj.nomaj import Resp
from nomaj.body import BodyOf


def rs_dumped(j: JSON, rs: Resp = Resp(status=200), dumps=json.dumps) -> Failable[Resp]:
    try:
        return Ok(
            replace(
                rs,
                body=BodyOf(dumps(j)),
            )
        )
    except TypeError as e:
        return Err(e)


def rs_nvelope_dumped(
    nvlp: Compound, rs: Resp = Resp(status=200), dumps=json.dumps
) -> Failable[Resp]:
    try:
        j = nvlp.as_json()
    except NvelopeError as e:
        return Err(e)
    return rs_dumped(j, rs, dumps)
