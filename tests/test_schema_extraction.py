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
    # After making abstract classes marker-only, only non-abstract endpoint
    # relationships remain here.
    assert len(rels) == 2

    # Spot check a couple of entries for correct labels and snake_case keys
    names = {r.name for r in rels}
    assert {"ListedOn", "QuoteOfListing"} == names

    # Spot check endpoint keys for remaining relations
    listed_on = next(r for r in rels if r.name == "ListedOn")
    assert listed_on.from_label == "Listing"
    assert listed_on.to_label == "TradingVenue"
    assert listed_on.from_key == "listing"
    assert listed_on.to_key == "trading_venue"

    quote_of_listing = next(r for r in rels if r.name == "QuoteOfListing")
    assert quote_of_listing.from_label == "Quote"
    assert quote_of_listing.to_label == "Listing"
    assert quote_of_listing.from_key == "quote"
    assert quote_of_listing.to_key == "listing"
