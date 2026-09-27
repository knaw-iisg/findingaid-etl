"""Small lxml-based helpers for navigating EAD 2002 XML."""

from __future__ import annotations

from lxml import etree

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "ead": "urn:isbn:1-931666-22-9",
    "xlink": "http://www.w3.org/1999/xlink",
}

# The <c01>..<c12> plus the level-agnostic <c> -- EAD allows either a fixed
# numbered nesting or unnumbered <c> at any depth; a real document uses one
# style consistently, but nothing stops mixing them, so both are handled.
COMPONENT_TAGS = ["c"] + [f"c{n:02d}" for n in range(1, 13)]


def parse(xml_bytes: bytes) -> etree._Element:
    return etree.fromstring(xml_bytes)


def find(el: etree._Element, path: str) -> etree._Element | None:
    return el.find(path, NS)


def findall(el: etree._Element, path: str) -> list[etree._Element]:
    return el.findall(path, NS)


def text_of(el: etree._Element | None) -> str | None:
    """All descendant text, whitespace-normalized -- markup (e.g. an inline
    <emph> or <num>) is dropped, keeping just the text content. A documented
    simplification vs. ead2rico's XMLLiteral output, which preserves inline
    markup; plain text is far simpler to produce correctly and is what
    matters for search/discovery use of this RDF.

    Text nodes are joined with a space: adjacent sibling elements in EAD
    (e.g. <head>Label</head><p>Text</p> with no whitespace between the
    tags) would otherwise run together into one unspaced word.
    """
    if el is None:
        return None
    text = " ".join(t for t in el.itertext() if t.strip())
    normalized = " ".join(text.split())
    return normalized or None


def direct_children(el: etree._Element, *local_names: str) -> list[etree._Element]:
    """Direct (non-recursive) children matching any of the given local
    (unprefixed) tag names, in document order."""
    names = set(local_names)
    return [c for c in el if etree.QName(c).localname in names]


def xlink_attr(el: etree._Element, name: str) -> str | None:
    return el.get(f"{{{NS['xlink']}}}{name}")


def record_from_oai(record_el: etree._Element) -> dict | None:
    """Extract ``{"header": {"identifier", "datestamp"}, "ead": <element>}``
    from one OAI-PMH ``<record>`` element (as found in both a cached
    GetRecord/ListRecords response and a live harvest)."""
    header = find(record_el, "oai:header")
    ead_root = find(record_el, "oai:metadata/ead:ead")
    if header is None or ead_root is None:
        return None
    identifier = find(header, "oai:identifier")
    datestamp = find(header, "oai:datestamp")
    return {
        "header": {
            "identifier": identifier.text if identifier is not None else None,
            "datestamp": datestamp.text if datestamp is not None else None,
        },
        "ead": ead_root,
    }
