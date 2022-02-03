from urllib.parse import ParseResult


def href(p: ParseResult) -> str:
    """
    Extract path and query from url
    """
    if p.query:
        return f"{p.path}?{p.query}"
    return p.path
