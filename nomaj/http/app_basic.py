from urllib.parse import urlparse

from multidict import CIMultiDict, CIMultiDictProxy
from koda import Result, Err

from nomaj.http_exception import HttpException
from nomaj.nomaj import Nomaj, Req, Resp
from nomaj.body import EmptyBody, BodyFromASGI


class AppBasic:
    def __init__(self, nomaj: Nomaj):
        self._nomaj: Nomaj = nomaj

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        elif scope["type"] == "http":
            maybe_resp: Result[Resp, Exception] = await self._nomaj.respond_to(
                Req(
                    uri=urlparse(scope["path"]),
                    method=scope["method"],
                    headers=CIMultiDictProxy(
                        CIMultiDict(
                            [(k.decode(), v.decode()) for k, v in scope["headers"]]
                        )
                    ),
                    body=BodyFromASGI(receive),
                )
            )
            if isinstance(maybe_resp, Err):
                err = maybe_resp.val
                resp = (
                    err.response
                    if isinstance(err, HttpException)
                    else Resp(
                        status=500,
                        headers=CIMultiDict(),
                        body=EmptyBody(),
                    )
                )
            else:
                resp = maybe_resp.val
            await _respond(resp, send)


async def _respond(response: Resp, send):
    await send(
        {
            "type": "http.response.start",
            "status": response.status,
            "headers": [
                (name.encode(), value.encode())
                for name, value in response.headers.items()
            ],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": await response.body.read(),
            "more_body": False,
        }
    )
