def merge_node(label: str, key: str) -> str:
    return f"""
    MERGE (n:{label} {{{key}: $key_value}})
    SET n += $props
    """

def merge_relationship(rel_type: str, from_label: str, from_key: str, to_label: str, to_key: str) -> str:
    return f"""
    MATCH (a:{from_label} {{{from_key}: $from_value}})
    MATCH (b:{to_label} {{{to_key}: $to_value}})
    MERGE (a)-[r:{rel_type}]->(b)
    SET r += $props
    """
