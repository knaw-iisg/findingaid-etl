"""Per-record EAD -> RDF pipeline."""

from __future__ import annotations

from rdflib import RDF, Graph, URIRef

from . import nde_ap
from .component import map_component
from .components import walk_dsc
from .context import mint_id
from .ead import find
from .prefixes import COLLECTION, SDO
from .recordsettype import additional_type

_OAI_ID_PREFIX = "oai:socialhistoryservices.org:"


def item_iri_from_record(record: dict) -> URIRef | None:
    """Same identifier convention as archive-etl: ``oai:...:10622/ARCHID``
    -> ``collection:ARCHID`` -- so both datasets describe the same resource."""
    identifier = record.get("header", {}).get("identifier")
    if not identifier:
        return None
    local = identifier[len(_OAI_ID_PREFIX):] if identifier.startswith(_OAI_ID_PREFIX) else identifier
    parts = local.split("/", 1)
    if len(parts) != 2 or not parts[1]:
        return None
    return COLLECTION[mint_id(parts[1])]


def process_record(record: dict, g: Graph) -> URIRef | None:
    """Process one OAI-harvested EAD record (``{"header": ..., "ead": <lxml
    element>}``, the shape produced by both ``fixtures.load_fixture`` and
    ``harvest.harvest_records``) into ``g``. Returns the minted top-level
    item IRI, or ``None`` if the record has no usable identifier."""
    item = item_iri_from_record(record)
    if item is None:
        return None

    ead_root = record.get("ead")
    if ead_root is None:
        return item

    archdesc = find(ead_root, "ead:archdesc")
    if archdesc is None:
        return item

    g.add((item, RDF.type, SDO.ArchiveComponent))
    rdf_type = additional_type(archdesc.get("level"))
    if rdf_type is not None:
        g.add((item, SDO.additionalType, rdf_type))

    map_component(g, item, archdesc)
    walk_dsc(g, archdesc, str(item))

    nde_ap.enrich(item, record, g)

    return item
