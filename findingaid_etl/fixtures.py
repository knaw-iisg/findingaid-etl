"""Loading ``static/findingaid/sourceData/*.xml`` fixtures -- each a cached
``GetRecord``/``metadataPrefix=ead`` OAI-PMH response."""

from __future__ import annotations

from pathlib import Path

from .ead import find, parse, record_from_oai


def load_fixture(path: Path) -> dict | None:
    root = parse(path.read_bytes())
    record = find(root, "oai:GetRecord/oai:record")
    if record is None:
        record = find(root, "oai:ListRecords/oai:record")
    if record is None:
        return None
    return record_from_oai(record)
