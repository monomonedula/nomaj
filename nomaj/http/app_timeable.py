import asyncio

from nomaj.http.app import App


class AppTimeable:
    def __init__(self, app: App, timeout: float):
        self._app: App = app
        self._timeout: float = timeout

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            await asyncio.wait_for(
                self._app(scope, receive, send),
                timeout=self._timeout,
            )
        else:
            await self._app(scope, receive, send)
