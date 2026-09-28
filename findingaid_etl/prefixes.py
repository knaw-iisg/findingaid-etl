"""Namespace/prefix declarations. Reuses archive-etl's ``collection:``/
``iisgv:``/``sdo:``/``dataset:`` namespaces so the two datasets interlink
correctly, and adds the RiC-O record-set-type vocabulary and the Library of
Congress ISO 639-2 language vocabulary this pipeline also needs."""

from rdflib import Namespace

BASE = "https://iisg.amsterdam/"
ID = BASE + "id/"

COLLECTION = Namespace(ID + "collection/")
IISGV = Namespace(BASE + "vocab/")
DATASET = Namespace(ID + "dataset/")

SDO = Namespace("https://schema.org/")
RICO_RECORD_SET_TYPES = Namespace("https://www.ica.org/standards/RiC/vocabularies/recordSetTypes#")
LOC_ISO639_2 = Namespace("http://id.loc.gov/vocabulary/iso639-2/")

DEFAULT_GRAPH = "https://iisg.amsterdam/graph/findingaid"

NAMESPACE_BINDINGS = {
    "collection": COLLECTION,
    "iisgv": IISGV,
    "dataset": DATASET,
    "sdo": SDO,
    "ricrst": RICO_RECORD_SET_TYPES,
    "iso639-2": LOC_ISO639_2,
}
