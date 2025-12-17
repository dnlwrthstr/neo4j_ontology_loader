from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from neo4j import Driver, Session

from .driver import create_driver


@contextmanager
def get_session(driver: Optional[Driver] = None, *, database: Optional[str] = None) -> Iterator[Session]:
    """
    Context manager that yields a Neo4j Session.

    If no Driver is provided, a temporary Driver will be created from settings
    and closed automatically when the context exits.
    """
    owns_driver = False
    if driver is None:
        driver = create_driver()
        owns_driver = True
    try:
        with driver.session(database=database) as session:
            yield session
    finally:
        if owns_driver:
            driver.close()


def run_query(
    query: str,
    parameters: Optional[dict] = None,
    *,
    database: Optional[str] = None,
    driver: Optional[Driver] = None,
) -> list[dict]:
    """Run a Cypher query and return a list of records as dicts.

    This is a convenience helper for simple, ad-hoc queries.
    """
    with get_session(driver, database=database) as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]
