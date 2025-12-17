"""DDL helpers specific to SZKB CSV loading performance.

This module contains non-unique indexes that speed up MERGE/lookup operations
for labels/properties that are only present in the SZKB load and not part of
the core ontology schema constraints.
"""


def szkb_loading_indexes() -> list[str]:
    statements: list[str] = []
    # Synthetic ids used during CSV load for these labels; add non-unique indexes
    # to speed up MERGE operations. Constraints for core ontology labels are
    # handled by ddl_schema.constraint_cypher based on model definitions.
    statements.append(
        "CREATE INDEX IF NOT EXISTS FOR (n:CrossCurrencyRate) ON (n.id)"
    )
    # Relationship creation for Quote -> Listing matches Quote by listing_id,
    # not by the synthetic Quote.id. Index listing_id to accelerate MATCH.
    statements.append(
        "CREATE INDEX IF NOT EXISTS FOR (n:Quote) ON (n.listing_id)"
    )
    return statements
