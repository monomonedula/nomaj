from abc import ABC, abstractmethod
from typing import Optional, Mapping, Union

from nomaj.failable import Failable, Ok, err_
from nomaj.fk.fallback.fallback import NjFallback, FbStatus
from nomaj.fk.fork.fk_chain import FkChain
from nomaj.fk.fork.fk_fixed import FkFixed
from nomaj.fk.fork.fk_methods import FkMethods
from nomaj.fk.fork.nj_fork import NjFork
from nomaj.fork import Fork
from nomaj.http.app_basic import AppBasic
from nomaj.misc.url import Path, PathParam
from nomaj.nomaj import Nomaj, Req, Resp
from nomaj.rq.json import json_of
from nomaj.rs.rs_dumped import rs_dumped
import sqlite3


class Endpoint(ABC):
    @abstractmethod
    async def respond_to(self, req: Req, path_params: Mapping[str, str]) -> Failable[Resp]:
        pass

    @abstractmethod
    def method(self) -> Optional[str]:
        pass


class FkEp(Fork):
    def __init__(self, p: Path, resp: Union[Endpoint, Nomaj, Fork]):
        self._path = p
        self._fk: Fork
        if isinstance(resp, Endpoint):
            self._fk = FkMethods(
                resp.method(),
                resp=NjEp(p, resp),
            )
        elif isinstance(resp, Nomaj):
            self._fk = FkFixed(resp)
        else:
            self._fk = resp

    def route(self, request: Req) -> Failable[Optional[Nomaj]]:
        if self._path.matches(request.uri.path):
            return self._fk.route(request)
        return Ok(None)

    def path(self):
        return self._path


class NjEp(Nomaj):
    def __init__(self, p: Path, e: Endpoint):
        self._e = e
        self._p = p

    async def respond_to(self, request: Req) -> Failable[Resp]:
        return await self._e.respond_to(
            request,
            self._p.path_params_of(request.uri.path).value()
        )


class EpHostsGetMany(Endpoint):
    def __init__(self, conn: sqlite3.Connection):
        self._conn: sqlite3.Connection = conn

    async def respond_to(self, req: Req, path_params: Mapping[str, str]) -> Failable[Resp]:
        return rs_dumped(
            [
                {"id": row[0], "host": row[1], "project_id": row[2]}
                for row in self._conn.cursor().execute(
                    "SELECT rowid, host, project_id FROM hosts"
                )
            ]
        )

    def method(self) -> Optional[str]:
        return "GET"


class EpHostsGetOne(Endpoint):
    def __init__(self, conn: sqlite3.Connection, host_id: PathParam[int]):
        self._conn: sqlite3.Connection = conn
        self._host_id: PathParam[int] = host_id

    async def respond_to(self, req: Req, path_params: Mapping[str, str]) -> Failable[Resp]:
        host_id = self._host_id.extract(path_params).value()
        row = (
            self._conn.cursor()
                .execute(
                "select rowid, host, project_id from hosts where rowid = ?", [host_id]
            ).fetchone()
        )
        if row:
            return rs_dumped({"id": row[0], "host": row[1], "project_id": row[2]})
        return rs_dumped(
            {"error": "not found"},
        )

    def method(self) -> Optional[str]:
        return "GET"


class EpHostsPost(Endpoint):
    def __init__(self, conn: sqlite3.Connection):
        self._conn: sqlite3.Connection = conn

    async def respond_to(self, req: Req, path_params: Mapping[str, str]) -> Failable[Resp]:
        j = await json_of(req)
        if j.err():
            return err_(j)
        data = j.value()
        c = self._conn.cursor()
        c.execute("INSERT INTO hosts VALUES (?, ?)", (data["host"], data["project_id"]))
        self._conn.commit()
        row = (
            self._conn.cursor()
                .execute(
                "select rowid, host, project_id from hosts where rowid = ?",
                [c.lastrowid],
            ).fetchone()
        )
        return rs_dumped({"id": row[0], "host": row[1], "project_id": row[2]})

    def method(self) -> Optional[str]:
        return "POST"


conn = sqlite3.connect("sf.db")
conn.execute("CREATE TABLE IF NOT EXISTS hosts (host TEXT, project_id TEXT)")
conn.commit()


hosts_path = Path("/hosts/")


app = AppBasic(
    NjFallback(
        NjFork(
            FkEp(
                hosts_path.as_prefix(),
                FkChain(
                    FkEp(
                        hosts_path.with_postfix("{host_id:int}"),
                        EpHostsGetOne(conn, PathParam("host_id", int))
                    ),
                    FkEp(
                        hosts_path,
                        EpHostsGetMany(conn),
                    ),
                    FkEp(
                        hosts_path,
                        EpHostsPost(conn)
                    )
                )
            ),
        ),
        FbStatus(),
    )
)



