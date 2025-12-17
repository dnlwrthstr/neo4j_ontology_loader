import re
from pydantic import BaseModel, Field

from neo4j_ontology_loader.schema.extract import (
    infer_key,
    extract_node_type,
    extract_rel_type,
    all_relationship_types,
)
from neo4j_ontology_loader.schema.ddl import constraint_cypher

# Built-in domain models
from neo4j_ontology_loader.models.instrument_type import InstrumentType
from neo4j_ontology_loader.models.trading_venue import TradingVenue
from neo4j_ontology_loader.models.cross_currency_rate import CrossCurrencyRate
from neo4j_ontology_loader.models.types import FinancialInstrument as FI


class NodeOne(BaseModel):
    foo: int
    bar: str


class NodeTwo(BaseModel):
    alpha: str
    beta: int | None = None


def test_infer_key_snake_case_for_builtin_models():
    assert infer_key(InstrumentType) == "instrument_type"
    assert infer_key(TradingVenue) == "trading_venue"
    assert infer_key(CrossCurrencyRate) == "cross_currency_rate"
    assert infer_key(FI) == "financial_instrument"


def test_extract_node_type_collects_properties_and_flags():
    class TestModel(BaseModel):
        id: str = Field(..., json_schema_extra={"unique": True})
        code: str = Field(..., json_schema_extra={"unique": True})
        optional_field: str | None = None

    node = extract_node_type(TestModel)
    assert node.name == "TestModel"
    assert node.key == "test_model"

    props = {p.name: p for p in node.properties}
    assert props["id"].unique is True
    assert props["code"].unique is True

    assert props["id"].required is True
    assert props["code"].required is True
    assert props["optional_field"].required is False


def test_constraint_cypher_contains_unique_and_not_null():
    class TestModel(BaseModel):
        id: str = Field(..., json_schema_extra={"unique": True})
        code: str = Field(..., json_schema_extra={"unique": True})

    node = extract_node_type(TestModel)
    cyphers = constraint_cypher(node)

    # Unique constraints for id and code
    assert (
        f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node.name}) REQUIRE n.id IS UNIQUE"
        in cyphers
    )
    assert (
        f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node.name}) REQUIRE n.code IS UNIQUE"
        in cyphers
    )

    # At least one NOT NULL constraint for a required field
    assert any(
        stmt
        == f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node.name}) REQUIRE n.id IS NOT NULL"
        for stmt in cyphers
    )


def test_extract_rel_type_custom_models():
    rel = extract_rel_type("RELATES_TO", NodeOne, NodeTwo)
    assert rel.name == "RELATES_TO"
    assert rel.from_label == "NodeOne"
    assert rel.to_label == "NodeTwo"
    assert rel.from_key == "node_one"
    assert rel.to_key == "node_two"


def test_all_relationship_types_structure_and_keys():
    rels = all_relationship_types()
    # Expect 7 definitions from the project mapping
    assert len(rels) == 7

    # Spot check a couple of entries for correct labels and snake_case keys
    names = {r.name for r in rels}
    assert {
        "IssuedBy",
        "UltimatelyIssuedBy",
        "HasType",
        "MainTradingPlace",
        "ListingOfInstrument",
        "ListedOn",
        "QuoteOfListing",
    } <= names

    # Find one relation and check endpoint keys
    has_type = next(r for r in rels if r.name == "HasType")
    assert has_type.from_label == "FinancialInstrument"
    assert has_type.to_label == "InstrumentType"
    assert has_type.from_key == "financial_instrument"
    assert has_type.to_key == "instrument_type"
