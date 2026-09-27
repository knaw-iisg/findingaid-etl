"""EAD ``@level`` -> RiC-O ``recordSetTypes`` vocabulary IRI. Ported from
ead2rico's ``set-recordsettype`` named template
(``sdo/xsl/named-templates.xsl``) -- only these five levels have a mapping
there; others (e.g. ``item``) are left untyped, same as upstream."""

from .prefixes import RICO_RECORD_SET_TYPES

LEVEL_TO_TYPE = {
    "fonds": RICO_RECORD_SET_TYPES.Fonds,
    "collection": RICO_RECORD_SET_TYPES.Collection,
    "series": RICO_RECORD_SET_TYPES.Series,
    "subseries": RICO_RECORD_SET_TYPES.Subseries,
    "file": RICO_RECORD_SET_TYPES.File,
}


def additional_type(level: str | None):
    if not level:
        return None
    return LEVEL_TO_TYPE.get(level)
