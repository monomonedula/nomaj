from typing import Union
import hmac
import hashlib


from abc import ABC, abstractmethod


class Signature(ABC):
    """
    A signature
    """

    @abstractmethod
    def sign(self, data: bytes) -> bytes:
        """
        Accept some data and return its signature.

        :param data: data to be signed
        :type data: ``bytes``

        :returns: signature calculated from the input
        :rtype: ``bytes``
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """
        :returns: name of the signature
        :rtype: ``str``
        """
        pass

    @abstractmethod
    def length(self) -> int:
        """
        :returns: length of the signature in bytes
        :rtype: ``int``
        """
        pass


class SiHmac(Signature):
    """
    One of SHA hashes (SHA256, SHA384, SHA512)

    :param key: secret key for SHA algorithm
    :type key: ``bytes`` or ``str``

    :param bits: bit length of the SHA function (256, 384 or 512). Defaults to 256
    :type bits: ``int``
    """

    _algorithm = {
        256: hashlib.sha256,
        384: hashlib.sha384,
        512: hashlib.sha512,
    }

    def __init__(self, key: Union[bytes, str], bits: int = 256):
        assert bits in self._algorithm
        self._key: bytes = key if isinstance(key, bytes) else key.encode()
        self._bits: int = bits

    def sign(self, data: bytes) -> bytes:
        return hmac.new(self._key, data, self._algorithm[self._bits]).digest()

    def name(self) -> str:
        return f"HS{self._bits}"

    def length(self) -> int:
        return int(self._bits / 8)
