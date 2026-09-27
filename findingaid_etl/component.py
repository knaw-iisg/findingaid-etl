"""Maps one EAD structural element (``<archdesc>`` or a ``<c>``/``<c01>``-
``<c12>`` component) to RDF triples on a given subject IRI. Shared by both
the top-level record (``pipeline.py``) and every nested component
(``components.py``), since EAD repeats the same ``<did>`` block plus a
common set of descriptive ("non-did") elements at every level.

Property choices are ported from ead2rico's ``sdo/xsl/did.xsl`` and
``sdo/xsl/non-did.xsl``, preferring archive-etl's existing ``iisgv:``
predicates over ead2rico's schema.org-only choices where a direct analog
already exists (e.g. ``iisgv:arrangement`` instead of a generic
``sdo:description``), so the two IISG datasets stay consistent for
concepts they share.
"""

from __future__ import annotations

from rdflib import XSD, Graph, Literal, URIRef

from .ead import direct_children, findall, text_of, xlink_attr
from .entities import add_creator, add_subjects
from .prefixes import IISGV, LOC_ISO639_2, SDO

# local tag name -> predicate, for the straightforward "element's text ->
# one literal triple" non-did elements. Elements with no entry here and no
# special handling below (accruals, appraisal, bibliography, fileplan,
# index, indexentry, namegrp, a bare non-did <note>) are intentionally
# dropped, matching ead2rico's own empty templates for them.
_SIMPLE_TEXT_PREDICATES = {
    "acqinfo": SDO.description,
    "altformavail": SDO.description,
    "arrangement": IISGV.arrangement,
    "bioghist": IISGV.biography,
    "custodhist": SDO.description,
    "odd": SDO.description,
    "originalsloc": IISGV.locationOfOriginals,
    "otherfindaid": SDO.description,
    "phystech": SDO.description,
    "prefercite": IISGV.preferCite,
    "processinfo": SDO.description,
    "relatedmaterial": IISGV.seeAlso,
    "scopecontent": SDO.abstract,
    "separatedmaterial": SDO.description,
    "userestrict": SDO.usageInfo,
}


def map_component(g: Graph, subject: URIRef, el) -> None:
    did = direct_children(el, "did")
    if did:
        _map_did(g, subject, did[0])

    for accessrestrict in direct_children(el, "accessrestrict"):
        text = text_of(accessrestrict)
        if text:
            g.add((subject, IISGV.access, Literal(text)))

    for tag, predicate in _SIMPLE_TEXT_PREDICATES.items():
        for child in direct_children(el, tag):
            text = text_of(child)
            if text:
                g.add((subject, predicate, Literal(text)))

    for controlaccess in direct_children(el, "controlaccess"):
        add_subjects(g, subject, controlaccess)

    for daogrp in direct_children(el, "daogrp", "dao"):
        _map_digital_objects(g, subject, daogrp)


def _map_did(g: Graph, subject: URIRef, did_el) -> None:
    for unitid in direct_children(did_el, "unitid"):
        text = text_of(unitid)
        if text:
            g.add((subject, SDO.identifier, Literal(text)))

    for unittitle in direct_children(did_el, "unittitle"):
        text = text_of(unittitle)
        if text:
            g.add((subject, SDO.name, Literal(text)))

    for unitdate in direct_children(did_el, "unitdate"):
        text = text_of(unitdate)
        if text:
            g.add((subject, SDO.temporalCoverage, Literal(text)))

    for physdesc in direct_children(did_el, "physdesc"):
        text = text_of(physdesc)
        if text:
            g.add((subject, IISGV.physicalDescription, Literal(text)))

    for physloc in direct_children(did_el, "physloc"):
        text = text_of(physloc)
        if text:
            g.add((subject, SDO.itemLocation, Literal(text)))

    for repository in direct_children(did_el, "repository"):
        # <repository> commonly nests a <corpname> plus a full postal
        # <address> block; the institution name alone (matching
        # archive-etl's iisgv:publisher, sourced from MARC 852) is more
        # useful here than "name + full address" run together.
        corpname = direct_children(repository, "corpname")
        text = text_of(corpname[0]) if corpname else text_of(repository)
        if text:
            g.add((subject, IISGV.publisher, Literal(text)))

    for abstract in direct_children(did_el, "abstract"):
        text = text_of(abstract)
        if text:
            g.add((subject, SDO.abstract, Literal(text)))

    for note in direct_children(did_el, "note"):
        text = text_of(note)
        if text:
            g.add((subject, SDO.description, Literal(text)))

    for origination in direct_children(did_el, "origination"):
        add_creator(g, subject, origination)

    for langmaterial in direct_children(did_el, "langmaterial"):
        for language in findall(langmaterial, "ead:language"):
            code = language.get("langcode")
            if code:
                g.add((subject, SDO.inLanguage, LOC_ISO639_2[code]))

    for daogrp in direct_children(did_el, "daogrp", "dao"):
        _map_digital_objects(g, subject, daogrp)


def _map_digital_objects(g: Graph, subject: URIRef, daogrp_el) -> None:
    """``<daogrp>``'s ``<daoloc>`` children (or a bare ``<dao>``), matching
    ead2rico's ``dao-iish.xsl``: a ``catalog``-labeled link is IISG's native
    viewer, a ``manifest``-labeled one feeds the IIIF universal viewer.
    ``thumbnail``-labeled links aren't mapped (same as upstream).
    """
    locs = direct_children(daogrp_el, "daoloc") or [daogrp_el]
    for loc in locs:
        label = xlink_attr(loc, "label")
        href = xlink_attr(loc, "href")
        if not href:
            continue
        if label == "catalog":
            g.add((subject, IISGV.nativeViewer, Literal(href, datatype=XSD.anyURI)))
        elif label == "manifest":
            url = f"https://access.iisg.amsterdam/universalviewer/#?manifest={href}"
            g.add((subject, SDO.contentUrl, URIRef(url)))
