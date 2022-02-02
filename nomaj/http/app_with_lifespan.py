from typing import Callable, Awaitable, Optional

from nomaj.http.app import App


class AppWithLifespan:
    def __init__(
        self,
        app: App,
        *,
        startup: Optional[Callable[[], Awaitable[None]]] = None,
        shutdown: Optional[Callable[[], Awaitable[None]]] = None,
    ):
        self._origin: App = app
        self._start: Optional[Callable[[], Awaitable[None]]] = startup
        self._stop: Optional[Callable[[], Awaitable[None]]] = shutdown

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    if self._start is not None:
                        await self._start()
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    if self._stop is not None:
                        await self._stop()
                    await send({"type": "lifespan.shutdown.complete"})
                    break
        else:
            await self._origin(scope, receive, send)
