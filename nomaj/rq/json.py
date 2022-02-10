import json

from nvelope import JSON

from koda import Result, Err, Ok
from nomaj.nomaj import Req


async def json_of(rq: Req, loads=json.loads) -> Result[JSON, Exception]:
    body: bytes = await rq.body.read()
    try:
        return Ok(loads(body))
    except json.JSONDecodeError as e:
        return Err(e)
