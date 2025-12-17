"""Backward-compatible DDL facade.

This module now re-exports schema creation helpers from ddl_schema to allow
progressive migration without breaking existing imports.
"""

from .ddl_schema import constraint_cypher
