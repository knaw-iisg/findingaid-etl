from urllib.parse import quote


def mint_id(local_id: str) -> str:
    """Percent-encode characters that aren't valid in an IRI path segment."""
    return quote(local_id, safe="")
