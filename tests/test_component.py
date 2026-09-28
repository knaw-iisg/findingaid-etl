"""Unit tests for individual mapping pieces, using small hand-built EAD
XML snippets (independent of the OAI fixtures)."""

from __future__ import annotations

from lxml import etree
from rdflib import Graph, URIRef
from rdflib.namespace import Namespace

from findingaid_etl.component import map_component
from findingaid_etl.ead import text_of

SDO = Namespace("https://schema.org/")
IISGV = Namespace("https://iisg.amsterdam/vocab/")

ITEM = URIRef("https://iisg.amsterdam/id/collection/TEST1")

_NSMAP = 'xmlns:ead="urn:isbn:1-931666-22-9"'


def _parse(fragment: str):
    return etree.fromstring(f'<ead:archdesc {_NSMAP}>{fragment}</ead:archdesc>')


def test_text_of_joins_adjacent_elements_with_space():
    el = _parse("<ead:accessrestrict><ead:head>Label</ead:head><ead:p>Body</ead:p></ead:accessrestrict>")
    accessrestrict = el.find("{urn:isbn:1-931666-22-9}accessrestrict")
    assert text_of(accessrestrict) == "Label Body"


def test_did_maps_identifier_name_date_language_creator():
    el = _parse(
        "<ead:did>"
        '<ead:unitid>ARCH00999</ead:unitid>'
        "<ead:unittitle>Test Papers</ead:unittitle>"
        '<ead:unitdate>1900-1950</ead:unitdate>'
        "<ead:langmaterial>"
        '<ead:language langcode="dut">Dutch</ead:language>'
        '<ead:language langcode="eng">English</ead:language>'
        "</ead:langmaterial>"
        '<ead:origination label="Creator"><ead:persname>Jane Doe</ead:persname></ead:origination>'
        "</ead:did>"
    )
    g = Graph()
    map_component(g, ITEM, el)

    assert (ITEM, SDO.identifier, None) in g
    names = {str(o) for o in g.objects(ITEM, SDO.identifier)}
    assert names == {"ARCH00999"}

    assert {str(o) for o in g.objects(ITEM, SDO.name)} == {"Test Papers"}
    assert {str(o) for o in g.objects(ITEM, SDO.temporalCoverage)} == {"1900-1950"}

    langs = {str(o).rsplit("/", 1)[-1] for o in g.objects(ITEM, SDO.inLanguage)}
    assert langs == {"dut", "eng"}

    creators = list(g.objects(ITEM, SDO.creator))
    assert len(creators) == 1
    assert (creators[0], SDO.name, None) in g


def test_controlaccess_produces_typed_subject_nodes():
    el = _parse(
        "<ead:controlaccess>"
        "<ead:head>Subjects</ead:head>"
        "<ead:geogname>Netherlands</ead:geogname>"
        "<ead:subject>Labour movements</ead:subject>"
        "</ead:controlaccess>"
    )
    g = Graph()
    map_component(g, ITEM, el)

    subjects = list(g.objects(ITEM, SDO.about))
    assert len(subjects) == 2
    subject_names = {str(g.value(s, SDO.name)) for s in subjects}
    assert subject_names == {"Netherlands", "Labour movements"}


def test_accessrestrict_and_arrangement_map_to_iisgv():
    el = _parse(
        "<ead:accessrestrict><ead:p>Restricted.</ead:p></ead:accessrestrict>"
        "<ead:arrangement><ead:p>Chronological.</ead:p></ead:arrangement>"
    )
    g = Graph()
    map_component(g, ITEM, el)

    assert (ITEM, IISGV.access, None) in g
    assert (ITEM, IISGV.arrangement, None) in g


def test_dao_catalog_and_manifest_links():
    el = _parse(
        "<ead:did>"
        "<ead:daogrp>"
        '<ead:daoloc xmlns:xlink="http://www.w3.org/1999/xlink" '
        'xlink:label="catalog" xlink:href="https://hdl.handle.net/10622/TEST.1?locatt=view:catalog"/>'
        '<ead:daoloc xmlns:xlink="http://www.w3.org/1999/xlink" '
        'xlink:label="manifest" xlink:href="https://hdl.handle.net/10622/TEST.1?locatt=view:manifest"/>'
        '<ead:daoloc xmlns:xlink="http://www.w3.org/1999/xlink" '
        'xlink:label="thumbnail" xlink:href="https://hdl.handle.net/10622/TEST.1?locatt=view:thumbnail"/>'
        "</ead:daogrp>"
        "</ead:did>"
    )
    g = Graph()
    map_component(g, ITEM, el)

    viewers = list(g.objects(ITEM, IISGV.nativeViewer))
    assert len(viewers) == 1
    assert str(viewers[0]) == "https://hdl.handle.net/10622/TEST.1?locatt=view:catalog"

    content_urls = list(g.objects(ITEM, SDO.contentUrl))
    assert len(content_urls) == 1
    assert "universalviewer" in str(content_urls[0])
