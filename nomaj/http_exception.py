from multidict import CIMultiDict

from nomaj.http.app_basic import EmptyBody
from nomaj.nomaj import Resp


class HttpException(Exception):
    @classmethod
    def from_status(cls, status: int, *args):
        return cls(
            Resp(
                status=status,
                headers=CIMultiDict(),
                body=EmptyBody(),
            ),
            *args
        )

    def __init__(self, resp: Resp, *args):
        super(HttpException, self).__init__(*args)
        self.response: Resp = resp
