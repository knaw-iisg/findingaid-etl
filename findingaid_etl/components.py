"""Recursive walker for the ``<dsc>``/``<c>``/``<c01>``-``<c12>`` component
hierarchy, minting one ``sdo:ArchiveComponent`` per node. Fragment-id scheme
ported from ead2rico's ``archdesc.xsl``: first-level children (direct
``<dsc>`` children) get ``#<position>``; every deeper level appends
``-<position>`` to its parent's fragment (``#1``, ``#1-1``, ``#1-1-1``, ...).
"""

from __future__ import annotations

from rdflib import RDF, Graph, Literal, URIRef

from .component import map_component
from .ead import COMPONENT_TAGS, direct_children
from .prefixes import SDO
from .recordsettype import additional_type


def walk_dsc(g: Graph, archdesc_el, base_iri: str) -> None:
    """Entry point: find every ``<dsc>`` directly under ``<archdesc>`` and
    walk its component children as the first level. Multiple ``<dsc>``
    siblings (rare) are treated as one continuous sibling sequence, so
    fragment ids stay unique -- ead2rico doesn't handle that case
    explicitly either.
    """
    all_children: list = []
    for dsc in direct_children(archdesc_el, "dsc"):
        all_children.extend(direct_children(dsc, *COMPONENT_TAGS))
    _walk_children(g, all_children, base_iri, parent_fragment=None, parent_subject=URIRef(base_iri))


def _walk_children(
    g: Graph,
    children: list,
    base_iri: str,
    *,
    parent_fragment: str | None,
    parent_subject: URIRef,
) -> None:
    for position, child in enumerate(children, start=1):
        fragment = str(position) if parent_fragment is None else f"{parent_fragment}-{position}"
        subject = URIRef(f"{base_iri}#{fragment}")

        g.add((subject, RDF.type, SDO.ArchiveComponent))
        g.add((subject, SDO.isPartOf, parent_subject))
        g.add((subject, SDO.position, Literal(position)))

        rdf_type = additional_type(child.get("level"))
        if rdf_type is not None:
            g.add((subject, SDO.additionalType, rdf_type))

        map_component(g, subject, child)

        grandchildren = direct_children(child, *COMPONENT_TAGS)
        if grandchildren:
            _walk_children(g, grandchildren, base_iri, parent_fragment=fragment, parent_subject=subject)
