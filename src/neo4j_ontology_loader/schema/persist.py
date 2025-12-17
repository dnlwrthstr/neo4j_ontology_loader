from neo4j import Driver
from neo4j_ontology_loader.schema.types import NodeTypeDef, RelTypeDef

ONTO_NODE = "NodeType"
ONTO_PROP = "PropertyDefinition"
ONTO_REL = "RelType"

def persist_schema(driver: Driver, node: NodeTypeDef) -> None:
    with driver.session() as session:
        session.execute_write(_persist_node_type, node)

def _persist_node_type(tx, node: NodeTypeDef) -> None:
    tx.run(
        f"MERGE (n:{ONTO_NODE} {{name: $name, key: $key}}) SET n.abstract = $abstract",
        name=node.name,
        key=node.key,
        abstract=getattr(node, "abstract", False),
    )

    for p in node.properties:
        tx.run(
            f"""
            MATCH (n:{ONTO_NODE} {{name: $node_name}})
            MERGE (p:{ONTO_PROP} {{node: $node_name, name: $prop_name}})
            SET p.type = $type, p.required = $required, p.unique = $unique
            MERGE (n)-[:HAS_PROPERTY]->(p)
            """,
            node_name=node.name,
            prop_name=p.name,
            type=p.type,
            required=p.required,
            unique=p.unique,
        )


def persist_relationship_types(driver: Driver, rels: list[RelTypeDef]) -> None:
    with driver.session() as session:
        for rel in rels:
            session.execute_write(_persist_rel_type, rel)


def _persist_rel_type(tx, rel: RelTypeDef) -> None:
    # Ensure endpoint node types exist (by name only; they should be persisted separately for full details)
    tx.run(f"MERGE (n:{ONTO_NODE} {{name: $name}})", name=rel.from_label)
    tx.run(f"MERGE (n:{ONTO_NODE} {{name: $name}})", name=rel.to_label)

    # Create relationship type node
    tx.run(
        f"MERGE (r:{ONTO_REL} {{name: $name}}) SET r.from_key=$from_key, r.to_key=$to_key",
        name=rel.name,
        from_key=rel.from_key,
        to_key=rel.to_key,
    )

    # Connect to endpoints
    tx.run(
        f"""
        MATCH (r:{ONTO_REL} {{name: $rel_name}})
        MATCH (from:{ONTO_NODE} {{name: $from_label}})
        MATCH (to:{ONTO_NODE} {{name: $to_label}})
        MERGE (r)-[:FROM]->(from)
        MERGE (r)-[:TO]->(to)
        """,
        rel_name=rel.name,
        from_label=rel.from_label,
        to_label=rel.to_label,
    )
