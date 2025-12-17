from neo4j import Driver


def clean_database(driver: Driver) -> None:
    """Drop all constraints and non-lookup indexes, then delete all nodes and relationships.

    Intended for maintenance/cleanup only. Destructive.
    """
    with driver.session() as session:
        # Drop all constraints (Neo4j 5 syntax)
        for record in session.run("SHOW CONSTRAINTS YIELD name RETURN name"):
            name = record["name"]
            session.run(f"DROP CONSTRAINT `{name}` IF EXISTS")

        # Drop all non-lookup indexes (avoid dropping token lookup indexes)
        for record in session.run(
            "SHOW INDEXES YIELD name, type WHERE type <> 'LOOKUP' RETURN name"
        ):
            name = record["name"]
            session.run(f"DROP INDEX `{name}` IF EXISTS")

        # Delete all relationships in batches to avoid large transaction memory usage
        session.run(
            """
            CALL () {
              MATCH ()-[r]-()
              WITH r LIMIT 100000
              DELETE r
            } IN TRANSACTIONS OF 10000 ROWS
            """
        )

        # Delete remaining nodes in batches
        session.run(
            """
            CALL () {
              MATCH (n)
              WITH n LIMIT 100000
              DETACH DELETE n
            } IN TRANSACTIONS OF 10000 ROWS
            """
        )
