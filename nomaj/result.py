from typing import Optional, Any, Dict


class Caught(Exception):
    def __init__(self, e: Exception, info: str, ctx: Optional[Dict[str, Any]] = None):
        self.e: Exception = e
        self.info: str = info
        self.ctx: Optional[Dict[str, Any]] = ctx
