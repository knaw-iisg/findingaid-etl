"""Origination (creator) and controlled-access (subject) name entities.
Ported from ead2rico's ``sdo/xsl/names.xsl``: each name element becomes a
blank node typed by its EAD element, with a plain ``sdo:name``.

No authority ids are minted -- the sampled records carry ``source="ingest"``
on these elements but not the ``@authfilenumber`` ead2rico's
``set-authorityURI`` template requires to build a real authority IRI, so
there's nothing usable to mint from (tracked as a follow-up, same category
as archive-etl's creator/authority gaps).
"""

from __future__ import annotations

from rdflib import RDF, BNode, Graph, Literal, URIRef

from .ead import direct_children, text_of
from .prefixes import SDO

_ABOUT_TYPES = {
    "corpname": SDO.Organization,
    "famname": SDO.Organization,
    "genreform": SDO.Thing,
    "geogname": SDO.Place,
    "name": SDO.Thing,
    "persname": SDO.Thing,
    "subject": SDO.Thing,
}
# persname under controlaccess is a named individual, not a generic Thing.
_ABOUT_TYPES["persname"] = SDO.Person

_CREATOR_TYPES = {
    "persname": SDO.Person,
    "corpname": SDO.Organization,
    "famname": SDO.Organization,
}


def add_creator(g: Graph, subject: URIRef, origination_el) -> None:
    """``<origination>`` (with a nested persname/corpname/famname) -> sdo:creator."""
    for tag, cls in _CREATOR_TYPES.items():
        for name_el in direct_children(origination_el, tag):
            name = text_of(name_el)
            if not name:
                continue
            node = BNode()
            g.add((subject, SDO.creator, node))
            g.add((node, RDF.type, cls))
            g.add((node, SDO.name, Literal(name)))


def add_subjects(g: Graph, subject: URIRef, controlaccess_el) -> None:
    """``<controlaccess>`` -> one ``sdo:about`` blank node per name/subject
    child (skipping the ``<head>`` label child)."""
    for tag, cls in _ABOUT_TYPES.items():
        for name_el in direct_children(controlaccess_el, tag):
            name = text_of(name_el)
            if not name:
                continue
            node = BNode()
            g.add((subject, SDO.about, node))
            g.add((node, RDF.type, cls))
            g.add((node, SDO.name, Literal(name)))
