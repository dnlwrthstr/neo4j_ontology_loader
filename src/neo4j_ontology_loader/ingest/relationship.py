from neo4j import Driver
from neo4j_ontology_loader.ingest.cypher_templates import merge_relationship

def ingest_relationships(
    driver: Driver,
    rel_type: str,
    from_label: str, from_key: str,
    to_label: str, to_key: str,
    rows: list[dict],
    from_field: str, to_field: str,
) -> None:
    cypher = merge_relationship(rel_type, from_label, from_key, to_label, to_key)
    with driver.session() as session:
        for row in rows:
            props = dict(row)
            from_value = props.pop(from_field)
            to_value = props.pop(to_field)
            session.run(cypher, from_value=from_value, to_value=to_value, props=props)
