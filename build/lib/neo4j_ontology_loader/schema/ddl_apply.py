from neo4j import Driver

def apply_cypher_statements(driver: Driver, statements: list[str]) -> None:
    with driver.session() as session:
        for stmt in statements:
            session.run(stmt)
