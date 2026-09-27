"""OAI-PMH harvesting of IISG's EAD finding aids, producing the same
``{"header": ..., "ead": <element>}`` shape used by
``static/findingaid/sourceData/*.xml`` fixtures via ``ead.record_from_oai``."""

from __future__ import annotations

import time
from collections.abc import Iterator

import requests

from .ead import find, findall, parse, record_from_oai

ENDPOINT = "https://api.socialhistoryservices.org/solr/all/oai"
METADATA_PREFIX = "ead"
DEFAULT_SET = "iish.archieven"

_MAX_RETRIES = 5
_RETRY_BACKOFF_SECONDS = 3


def _get_with_retry(http: requests.Session, endpoint: str, params: dict, timeout: float) -> requests.Response:
    """A full harvest makes thousands of requests over tens of minutes;
    transient connection drops are expected, not exceptional (observed
    directly against this same endpoint during development)."""
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = http.get(endpoint, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
    raise last_error


def harvest_records(
    *,
    endpoint: str = ENDPOINT,
    metadata_prefix: str = METADATA_PREFIX,
    set_spec: str | None = DEFAULT_SET,
    identifier: str | None = None,
    session: requests.Session | None = None,
    timeout: float = 120,
    resume_token: str | None = None,
    on_page: callable = None,
) -> Iterator[dict]:
    """``resume_token`` restarts a previously interrupted ``ListRecords``
    harvest from that resumption token. ``on_page(resumption_token)`` is
    called after each page if given, so a caller can persist a checkpoint.
    """
    http = session or requests.Session()

    if identifier is not None:
        params = {"verb": "GetRecord", "identifier": identifier, "metadataPrefix": metadata_prefix}
        resp = _get_with_retry(http, endpoint, params, timeout)
        root = parse(resp.content)
        record_el = find(root, "oai:GetRecord/oai:record")
        if record_el is not None:
            record = record_from_oai(record_el)
            if record:
                yield record
        return

    initial_params = {"verb": "ListRecords", "metadataPrefix": metadata_prefix}
    if set_spec:
        initial_params["set"] = set_spec

    resumption_token = resume_token
    while True:
        request_params = {"verb": "ListRecords", "resumptionToken": resumption_token} if resumption_token else initial_params

        resp = _get_with_retry(http, endpoint, request_params, timeout)
        root = parse(resp.content)
        list_records = find(root, "oai:ListRecords")
        if list_records is None:
            return

        for record_el in findall(list_records, "oai:record"):
            record = record_from_oai(record_el)
            if record:
                yield record

        token_el = find(list_records, "oai:resumptionToken")
        token_text = token_el.text if token_el is not None else None
        if on_page is not None:
            on_page(token_text)
        if not token_text:
            return
        resumption_token = token_text
