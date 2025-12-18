from neo4j_ontology_loader.schema.types import EntityDef


def constraint_cypher(node: EntityDef) -> list[str]:
    cyphers: list[str] = []
    # Do not create constraints for abstract node types
    if getattr(node, "abstract", False):
        return cyphers
    # unique constraints
    for p in node.properties:
        if p.unique:
            cyphers.append(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node.name}) REQUIRE n.{p.name} IS UNIQUE"
            )
    # required constraints (Neo4j supports existence constraints; keep conservative)
    for p in node.properties:
        if p.required:
            cyphers.append(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node.name}) REQUIRE n.{p.name} IS NOT NULL"
            )
    return cyphers
