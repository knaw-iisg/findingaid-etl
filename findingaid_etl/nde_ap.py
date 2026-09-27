"""NDE Schema.org Application Profile enrichment, applied only to the
top-level record (not to every nested component -- see the plan: components
get structural ``sdo:isPartOf`` to their parent, but dataset-registration
properties belong to the record as a whole).

Same pattern as ``archive-etl``'s ``nde_ap.py``. ``dataset:findingaid`` is
kept distinct from archive-etl's ``dataset:archive``: these are two
independently harvestable OAI metadata formats/sets, each a legitimate
separate dataset, not the same one described twice.
"""

from __future__ import annotations

from rdflib import RDF, Graph, Literal, URIRef
from rdflib.namespace import XSD

from .prefixes import DATASET, SDO

DATASET_IRI = DATASET["findingaid"]


def _emit_dataset_description(g: Graph) -> None:
    if (DATASET_IRI, RDF.type, SDO.Dataset) in g:
        return
    g.add((DATASET_IRI, RDF.type, SDO.Dataset))
    g.add((DATASET_IRI, SDO.name, Literal("IISG Vindhulpmiddelen", lang="nl")))
    g.add((DATASET_IRI, SDO.name, Literal("IISH Finding Aids", lang="en")))
    g.add((DATASET_IRI, SDO.description, Literal(
        "Archiefinventarissen (vindhulpmiddelen) van het Internationaal Instituut "
        "voor Sociale Geschiedenis (IISG).", lang="nl",
    )))
    # TODO(IISG): sdo:license, sdo:includedInDataCatalog, sdo:accessRights --
    # same open question as archive-etl/biblio-etl's dataset nodes.


def enrich(item: URIRef, record: dict, g: Graph, *, dataset_iri: URIRef = DATASET_IRI) -> None:
    datestamp = record.get("header", {}).get("datestamp")
    if datestamp:
        g.add((item, SDO.sdDatePublished, Literal(str(datestamp), datatype=XSD.dateTime)))

    g.add((item, SDO.isPartOf, dataset_iri))
    _emit_dataset_description(g)
