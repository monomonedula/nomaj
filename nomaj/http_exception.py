class HttpException(Exception):
    def __init__(self, status: int, *args):
        super(HttpException, self).__init__(*args)
        self._status: int = status

    def code(self) -> int:
        return self._status
