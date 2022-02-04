import json

from nvelope import JSON

from nomaj.failable import Failable, Err, Ok
from nomaj.nomaj import Req


async def json_of(rq: Req, loads=json.loads) -> Failable[JSON]:
    body: bytes = await rq.body.read()
    try:
        return Ok(loads(body))
    except json.JSONDecodeError as e:
        return Err(e)
