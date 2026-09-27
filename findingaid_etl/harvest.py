"""OAI-PMH harvesting of IISG's EAD finding aids, producing the same
``{"header": ..., "ead": <element>}`` shape used by
``static/findingaid/sourceData/*.xml`` fixtures via ``ead.record_from_oai``."""

from __future__ import annotations

from collections.abc import Iterator

import requests

from .ead import find, findall, parse, record_from_oai

ENDPOINT = "https://api.socialhistoryservices.org/solr/all/oai"
METADATA_PREFIX = "ead"
DEFAULT_SET = "iish.archieven"


def harvest_records(
    *,
    endpoint: str = ENDPOINT,
    metadata_prefix: str = METADATA_PREFIX,
    set_spec: str | None = DEFAULT_SET,
    identifier: str | None = None,
    session: requests.Session | None = None,
    timeout: float = 120,
) -> Iterator[dict]:
    http = session or requests.Session()

    if identifier is not None:
        params = {"verb": "GetRecord", "identifier": identifier, "metadataPrefix": metadata_prefix}
        resp = http.get(endpoint, params=params, timeout=timeout)
        resp.raise_for_status()
        root = parse(resp.content)
        record_el = find(root, "oai:GetRecord/oai:record")
        if record_el is not None:
            record = record_from_oai(record_el)
            if record:
                yield record
        return

    params = {"verb": "ListRecords", "metadataPrefix": metadata_prefix}
    if set_spec:
        params["set"] = set_spec

    resumption_token = None
    while True:
        request_params = {"verb": "ListRecords", "resumptionToken": resumption_token} if resumption_token else params

        resp = http.get(endpoint, params=request_params, timeout=timeout)
        resp.raise_for_status()
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
        if not token_text:
            return
        resumption_token = token_text
