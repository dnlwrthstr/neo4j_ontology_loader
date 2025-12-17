from neo4j import Driver
from neo4j.exceptions import Neo4jError
from neo4j_ontology_loader.ingest.cypher_templates import merge_node
from utils.logging import get_logger
import math

def ingest_nodes(driver: Driver, label: str, key: str, rows: list[dict]) -> None:
    cypher = merge_node(label, key)
    logger = get_logger()
    with driver.session() as session:
        for row in rows:
            props = dict(row)
            # Skip rows without a usable key (None/NaN/empty string)
            if key not in props:
                logger.warning(
                    "ingest_nodes skip label=%s reason=missing-key key=%s row_keys=%s",
                    label,
                    key,
                    list(props.keys()),
                )
                continue

            key_value = props[key]
            if (
                key_value is None
                or (isinstance(key_value, float) and math.isnan(key_value))
                or (isinstance(key_value, str) and key_value.strip() == "")
            ):
                logger.warning(
                    "ingest_nodes skip label=%s reason=empty-key key=%s",
                    label,
                    key,
                )
                continue
            try:
                session.run(cypher, key_value=key_value, props=props)
            except Neo4jError as e:
                # Log and continue on violations (e.g., uniqueness/constraint errors)
                logger.error(
                    "ingest_nodes error label=%s key=%s value=%s props_keys=%s error=%s",
                    label,
                    key,
                    key_value,
                    list(props.keys()),
                    str(e),
                )
                continue
