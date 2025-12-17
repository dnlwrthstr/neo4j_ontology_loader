import logging
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_logger() -> logging.Logger:
    logger = logging.getLogger("neo4j_ontology_loader")
    if logger.handlers:
        return logger

    logger.setLevel(os.getenv("NOLO_LOG_LEVEL", "INFO").upper())

    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    log_file = os.getenv("NOLO_LOG_FILE")
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
