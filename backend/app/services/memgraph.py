import logging
from contextlib import contextmanager
from typing import Generator, Any
from neo4j import GraphDatabase, Driver, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

_driver: Driver | None = None


def get_driver() -> Driver:
    """Get or create the Memgraph Bolt driver (singleton)."""
    global _driver
    if _driver is None:
        auth = (
            (settings.MEMGRAPH_USER, settings.MEMGRAPH_PASSWORD)
            if settings.MEMGRAPH_USER
            else ("", "")
        )
        _driver = GraphDatabase.driver(
            settings.MEMGRAPH_URI,
            auth=auth,
            max_connection_pool_size=10,
            connection_timeout=10,
            encrypted=True,
        )
        logger.info(f"Memgraph driver created → {settings.MEMGRAPH_URI}")
    return _driver


def close_driver() -> None:
    """Close the driver cleanly on shutdown."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        logger.info("Memgraph driver closed.")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager yielding a Memgraph session."""
    driver = get_driver()
    session = driver.session()
    try:
        yield session
    finally:
        session.close()


def run_query(cypher: str, params: dict | None = None) -> list[dict[str, Any]]:
    """
    Execute a Cypher query and return results as a list of dicts.
    Use for all read and write operations.
    """
    with get_session() as session:
        result = session.run(cypher, params or {})
        return [record.data() for record in result]


def ping() -> bool:
    """Verify Memgraph connectivity. Returns True if reachable."""
    try:
        run_query("RETURN 1 AS alive")
        return True
    except Exception as exc:
        logger.warning(f"Memgraph ping failed: {exc}")
        return False