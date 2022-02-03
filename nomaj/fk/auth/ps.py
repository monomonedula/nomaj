from abc import abstractmethod, ABC

from nomaj.fk.auth.identity import Identity
from nomaj.failable import Failable
from nomaj.nomaj import Req, Resp


class Pass(ABC):
    """
    Pass to enter a user and let him exit.

    This interface is intended for authentication handling.
    """

    @abstractmethod
    async def enter(self, request: Req) -> Failable[Identity]:
        """
        Authenticate the user by the request.
        """
        pass

    @abstractmethod
    async def exit(self, response: Resp, identity: Identity) -> Failable[Resp]:
        """
        Maybe put some authentication credentials into the response.
        """
        pass
