"""Relationship Cypher helpers generated from schema.

These helpers intentionally cast both MATCH sides to string to make
relationship creation robust against mixed numeric/string types coming
from CSVs (e.g., 4411 vs "4411").
"""


def build_rel_cypher_casted(
    rel_type: str,
    from_label: str,
    from_prop: str,
    to_label: str,
    to_prop: str,
) -> str:
    """Return a Cypher statement that matches endpoints by casting both
    sides to string, then MERGEs the relationship type.

    Parameters are not interpolated as identifiers; only label/prop names
    are injected in the template, values are passed as parameters.
    """
    return f"""
    MATCH (a:{from_label})
    WHERE toString(a.{from_prop}) = toString($from_value)
    MATCH (b:{to_label})
    WHERE toString(b.{to_prop}) = toString($to_value)
    MERGE (a)-[r:{rel_type}]->(b)
    SET r += $props
    """
