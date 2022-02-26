from typing import Optional, Mapping, Dict
import sqlite3

from koda import Result, Err
from nvelope import JSON

from nomaj.api.endpoint import Endpoint
from nomaj.api.fk_ep import FkEp
from nomaj.fk.fallback.fallback import NjFallback, FbStatus, FbLog
from nomaj.fk.fork.fk_chain import FkChain
from nomaj.fk.fork.nj_fork import NjFork
from nomaj.http.app_basic import AppBasic
from nomaj.misc.url import PathParam, PathSimple
from nomaj.nomaj import Req, Resp
from nomaj.rq.json import json_of
from nomaj.rs.rs_dumped import rs_dumped
from nomaj.rs.rs_with_status import rs_with_status
from nomaj.api.swagger import traces, path_of, schema_of, methods_of


class EpHostsGetMany(Endpoint):
    def __init__(self, conn: sqlite3.Connection):
        self._conn: sqlite3.Connection = conn

    async def respond_to(
        self, req: Req, path_params: Mapping[str, str]
    ) -> Result[Resp, Exception]:
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

    def meta(self) -> Dict[str, JSON]:
        return {
            "endpoint": {
                "type": self.__class__.__name__,
            },
            "children": [],
        }


class EpHostsGetOne(Endpoint):
    def __init__(self, conn: sqlite3.Connection, host_id: PathParam[int]):
        self._conn: sqlite3.Connection = conn
        self._host_id: PathParam[int] = host_id

    async def respond_to(
        self, req: Req, path_params: Mapping[str, str]
    ) -> Result[Resp, Exception]:
        extracted = self._host_id.extract(path_params)
        if isinstance(extracted, Err):
            return extracted
        host_id = extracted.val
        row = (
            self._conn.cursor()
            .execute(
                "select rowid, host, project_id from hosts where rowid = ?", [host_id]
            )
            .fetchone()
        )
        if row:
            return rs_dumped({"id": row[0], "host": row[1], "project_id": row[2]})
        return rs_dumped({"error": "not found"}, rs_with_status(404))

    def method(self) -> Optional[str]:
        return "GET"

    def meta(self) -> Dict[str, JSON]:
        return {
            "endpoint": {
                "type": self.__class__.__name__,
                "responses": {
                    "200": {
                        "description": "A Host object",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                }
                            }
                        },
                    },
                    "400": {
                        "description": "Invalid host id",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                }
                            }
                        },
                    },
                    "404": {
                        "description": "A host with given ID is not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                }
                            }
                        },
                    },
                },
            },
            "children": [],
        }


class EpHostsPost(Endpoint):
    def __init__(self, conn: sqlite3.Connection):
        self._conn: sqlite3.Connection = conn

    async def respond_to(
        self, req: Req, path_params: Mapping[str, str]
    ) -> Result[Resp, Exception]:
        j = await json_of(req)
        if isinstance(j, Err):
            return j
        data = j.val
        c = self._conn.cursor()
        c.execute("INSERT INTO hosts VALUES (?, ?)", (data["host"], data["project_id"]))
        self._conn.commit()
        row = (
            self._conn.cursor()
            .execute(
                "select rowid, host, project_id from hosts where rowid = ?",
                [c.lastrowid],
            )
            .fetchone()
        )
        return rs_dumped({"id": row[0], "host": row[1], "project_id": row[2]})

    def method(self) -> Optional[str]:
        return "POST"

    def meta(self) -> Dict[str, JSON]:
        return {
            "endpoint": {
                "type": self.__class__.__name__,
            },
            "children": [],
        }


conn = sqlite3.connect("sf.db")
conn.execute("CREATE TABLE IF NOT EXISTS hosts (host TEXT, project_id TEXT)")
conn.commit()


hosts_path = PathSimple("/hosts/")

app = AppBasic(
    NjFallback(
        NjFork(
            FkEp(
                hosts_path.as_prefix(),
                FkChain(
                    FkEp(
                        hosts_path.with_postfix("{host_id:int}"),
                        EpHostsGetOne(conn, PathParam("host_id", int)),
                    ),
                    FkEp(
                        hosts_path,
                        EpHostsGetMany(conn),
                    ),
                    FkEp(hosts_path, EpHostsPost(conn)),
                ),
            ),
        ),
        FbLog(FbStatus()),
    )
)

meta = NjFallback(
    NjFork(
        FkEp(
            hosts_path.as_prefix(),
            FkChain(
                FkEp(
                    hosts_path.with_postfix("{host_id:int}"),
                    EpHostsGetOne(conn, PathParam("host_id", int)),
                ),
                FkEp(
                    hosts_path,
                    EpHostsGetMany(conn),
                ),
                FkEp(hosts_path, EpHostsPost(conn)),
            ),
        ),
    ),
    FbLog(FbStatus()),
).meta()

# print(traces(graph_of(meta))[0])
# print(traces(graph_of(meta))[1])
# print(traces(graph_of(meta))[2])

print("final", traces(meta)[0])
print("final", traces(meta)[1])
print("final", traces(meta)[2])

print("\n\n\n")

print("path", [path_of(t) for t in traces(meta)])
print("method", [methods_of(t) for t in traces(meta)])
print("sch", schema_of(traces(meta)))
