"""
Lightweight exports for schema utilities used in unit tests.

We intentionally do not import `.persist` here to avoid requiring the external
`neo4j` driver at import time for tests that only need extraction/DDL helpers.
"""

from .extract import extract_node_type, extract_rel_type, all_relationship_types
from .ddl import constraint_cypher
from .rel_cypher import build_rel_cypher_casted

__all__ = [
    "extract_node_type",
    "extract_rel_type",
    "all_relationship_types",
    "constraint_cypher",
    "build_rel_cypher_casted",
]
