from abc import abstractmethod, ABC
from typing import Dict

from koda import Result
from nvelope import JSON

from nomaj.fk.auth.identity import Identity
from nomaj.nomaj import Req, Resp


class Pass(ABC):
    """
    Pass to enter a user and let him exit.

    This interface is intended for authentication handling.
    """

    @abstractmethod
    async def enter(self, request: Req) -> Result[Identity, Exception]:
        """
        Authenticate the user by the request.
        """
        pass

    @abstractmethod
    async def exit(self, response: Resp, identity: Identity) -> Result[Resp, Exception]:
        """
        Maybe put some authentication credentials into the response.
        """
        pass

    @abstractmethod
    def meta(self) -> Dict[str, JSON]:
        pass
