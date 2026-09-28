"""Runs every static/findingaid/sourceData fixture through the full pipeline.

Given output size (up to ~9500 triples for the largest fixture), assertions
are structural rather than full-output diffing.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree
from rdflib import Graph, URIRef
from rdflib.namespace import XSD, Namespace

from findingaid_etl.ead import COMPONENT_TAGS, NS
from findingaid_etl.fixtures import load_fixture
from findingaid_etl.pipeline import process_record

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "static" / "findingaid" / "sourceData"
SDO = Namespace("https://schema.org/")
IISGV = Namespace("https://iisg.amsterdam/vocab/")


def _fixture_paths():
    return sorted(FIXTURES_DIR.glob("*.xml"))


def _xml_component_count(path: Path) -> int:
    root = etree.parse(str(path)).getroot()
    return sum(len(root.findall(f".//ead:{tag}", NS)) for tag in COMPONENT_TAGS)


@pytest.mark.parametrize("path", _fixture_paths(), ids=lambda p: p.stem)
def test_record_processes_without_error(path: Path):
    record = load_fixture(path)
    assert record is not None
    g = Graph()
    item = process_record(record, g)
    assert item is not None
    assert len(g) > 0


@pytest.mark.parametrize("path", _fixture_paths(), ids=lambda p: p.stem)
def test_component_count_matches_source_xml(path: Path):
    """The number of minted #-fragment component subjects must exactly
    match the number of <c>/<c01>-<c12> elements in the source EAD -- a
    strong structural correctness check (no dropped or duplicated nodes,
    no fragment-id collisions from the hierarchical minting scheme)."""
    record = load_fixture(path)
    g = Graph()
    item = process_record(record, g)

    expected = _xml_component_count(path)
    component_subjects = {
        s for s in g.subjects(SDO.isPartOf, None)
        if isinstance(s, URIRef) and str(s).startswith(f"{item}#")
    }
    assert len(component_subjects) == expected


def test_arch03414_top_level_and_component_fields():
    path = FIXTURES_DIR / "ARCH03414.xml"
    record = load_fixture(path)
    g = Graph()
    item = process_record(record, g)

    assert item == URIRef("https://iisg.amsterdam/id/collection/ARCH03414")

    names = {str(o) for o in g.objects(item, SDO.name)}
    assert "Archief Federatie Studentenwerkgroepen Homoseksualiteit (FSWH)" in names

    publishers = {str(o) for o in g.objects(item, IISGV.publisher)}
    assert publishers == {"IISG (Collectie IHLIA)"}

    creators = list(g.objects(item, SDO.creator))
    assert len(creators) == 1
    assert (creators[0], SDO.name, None) in g

    first_child = URIRef("https://iisg.amsterdam/id/collection/ARCH03414#1")
    assert (first_child, SDO.isPartOf, item) in g
    assert (first_child, SDO.position, None) in g


def test_nde_ap_dataset_link_and_typed_sd_date_published():
    record = load_fixture(FIXTURES_DIR / "ARCH03414.xml")
    g = Graph()
    item = process_record(record, g)

    assert (item, SDO.isPartOf, URIRef("https://iisg.amsterdam/id/dataset/findingaid")) in g
    dates = list(g.objects(item, SDO.sdDatePublished))
    assert dates
    assert dates[0].datatype == XSD.dateTime


def test_deep_nesting_and_digital_objects():
    """ARCH00018 has 4 levels of nesting and IISG digital-object links."""
    record = load_fixture(FIXTURES_DIR / "ARCH00018.xml")
    g = Graph()
    process_record(record, g)

    deep = URIRef("https://iisg.amsterdam/id/collection/ARCH00018#1-1-1-1")
    assert (deep, None, SDO.ArchiveComponent) in g
    assert list(g.objects(deep, IISGV.nativeViewer))
    assert list(g.objects(deep, SDO.contentUrl))
