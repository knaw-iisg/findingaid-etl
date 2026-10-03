# findingaid-etl

Maps IISG's OAI-PMH-harvested EAD 2002 finding aids (archival inventories) to
RDF: the full nested hierarchy of series/subseries/files/items, not just the
top-level collection description [archive-etl](https://github.com/knaw-iisg/archive-etl)
already covers from MARC. The top-level record reuses archive-etl's
`collection:<id>` IRI, so both datasets describe the same resource and
interlink via `sdo:isPartOf` rather than producing disconnected records for
one archive.

Property mapping decisions are ported from
[ivozandhuis/ead2rico](https://github.com/ivozandhuis/ead2rico)'s
schema.org-flavored XSLT (`sdo/xsl/*.xsl`), reimplemented here in Python +
lxml + rdflib, preferring archive-etl's existing `iisgv:` predicates over
ead2rico's schema.org-only choices where a direct analog already exists
(e.g. `iisgv:arrangement` instead of a generic `sdo:description`).

## Public instance

This pipeline's output is merged with six others into a single public
knowledge graph, browsable at **https://kb.zijdeman.nl** and queryable
directly at **https://sparql.zijdeman.nl** (or via QLever's own query UI
at **https://kg.zijdeman.nl**) -- see
[iisg-kb-viewer](https://github.com/knaw-iisg/iisg-kb-viewer) and
[triplestore](https://github.com/knaw-iisg/triplestore).

## Structure

```
collection:ARCH00018        # top-level record, from <archdesc>
collection:ARCH00018#1      # first-level component, sdo:isPartOf the above
collection:ARCH00018#1-1    # nested under #1
collection:ARCH00018#1-1-1  # ...and so on, however deep the EAD goes
```

Every `<c>`/`<c01>`-`<c12>` becomes its own `sdo:ArchiveComponent`. Verified
against real IISG records up to 4 levels deep and 933 components in a single
finding aid (`ARCH00031`), processed in well under a second.

**`sdo:name`/`sdo:description` are not language-tagged** -- same reasoning as
archive-etl: EAD's `langmaterial` describes the archived materials'
languages, not the finding-aid text's own language.

**Known simplification:** text is extracted as plain strings (markup like
inline `<emph>`/`<num>` is dropped), not as ead2rico's `rdf:XMLLiteral`
(which preserves inline HTML formatting). Simpler to get right, and what
matters for search/discovery use of this RDF.

## Install

```bash
python -m venv .venv
.venv/bin/pip install -e ".[test]"
```

## Run

```bash
# All sample records under static/findingaid/sourceData/:
python -m findingaid_etl.cli --source fixtures --out findingaid.ttl

# Just one record, printed to stdout:
python -m findingaid_etl.cli --source fixtures --record-id ARCH03414

# Live OAI-PMH (metadataPrefix=ead), one record:
python -m findingaid_etl.cli --source oai --record-id ARCH00018
```

## Test

```bash
.venv/bin/pytest
```

## Layout

- `findingaid_etl/ead.py` -- lxml namespace map + XPath/text helpers.
- `findingaid_etl/component.py` -- maps one `<did>` + sibling descriptive
  elements to triples on a subject; shared by the top-level record and every
  nested component.
- `findingaid_etl/components.py` -- recursive `<c>`/`<c01>`-`<c12>` walker,
  hierarchical fragment-id minting.
- `findingaid_etl/entities.py` -- creator/subject name entities.
- `findingaid_etl/recordsettype.py` -- `@level` -> RiC-O record-set-type IRI.
- `findingaid_etl/nde_ap.py` -- top-level-record-only NDE AP enrichment.
- `findingaid_etl/harvest.py` -- OAI-PMH client (`metadataPrefix=ead`);
  `static/findingaid/sourceData/` fixtures are cached real records in the
  same shape.
