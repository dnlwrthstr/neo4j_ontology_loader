from pydantic import BaseModel
from neo4j_ontology_loader.schema.types import NodeTypeDef, PropertyDef, RelTypeDef
import re
from neo4j_ontology_loader.models.issuer import Issuer
from neo4j_ontology_loader.models.instrument_type import InstrumentType
from neo4j_ontology_loader.models.trading_venue import TradingVenue
from neo4j_ontology_loader.models.listing import Listing
from neo4j_ontology_loader.models.quotes import Quote
from neo4j_ontology_loader.models.relationships import (
    IssuedBy,
    UltimatelyIssuedBy,
    HasType,
    MainTradingPlace,
    ListingOfInstrument,
    ListedOn,
    QuoteOfListing,
)

def infer_key(model: type[BaseModel]) -> str:
    """Infer ontology node type key from the class name.

    Convention: snake_case of the model class name in lowercase.
    Example: InstrumentType -> instrument_type
    """
    name = model.__name__
    # Convert CamelCase/PascalCase to snake_case
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    snake = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return snake

def extract_node_type(model: type[BaseModel], *, abstract: bool = False) -> NodeTypeDef:
    props: list[PropertyDef] = []
    for name, field in model.model_fields.items():
        extra = field.json_schema_extra or {}
        t = getattr(field.annotation, "__name__", str(field.annotation))
        props.append(PropertyDef(
            name=name,
            type=t,
            required=field.is_required(),
            unique=bool(extra.get("unique", False)),
        ))
    return NodeTypeDef(name=model.__name__, key=infer_key(model), properties=props, abstract=abstract)


def extract_rel_type(name: str, from_model: type[BaseModel], to_model: type[BaseModel]) -> RelTypeDef:
    return RelTypeDef(
        name=name,
        from_label=from_model.__name__,
        to_label=to_model.__name__,
        from_key=infer_key(from_model),
        to_key=infer_key(to_model),
    )


def all_relationship_types() -> list[RelTypeDef]:
    """Return all relationship type definitions based on current relationship models.

    Mapping is defined from the domain comments in models/relationships.py.
    """
    return [
        # Relationships from abstract FinancialInstrument to other entities
        extract_rel_type(IssuedBy.__name__, FI, Issuer),
        extract_rel_type(UltimatelyIssuedBy.__name__, FI, Issuer),
        extract_rel_type(HasType.__name__, FI, InstrumentType),
        extract_rel_type(MainTradingPlace.__name__, FI, TradingVenue),
        # Listing to FinancialInstrument
        extract_rel_type(ListingOfInstrument.__name__, Listing, FI),
        extract_rel_type(ListedOn.__name__, Listing, TradingVenue),
        extract_rel_type(QuoteOfListing.__name__, Quote, Listing),
    ]


# Extended property-as-relationship schema definitions for types in models/types.py
from neo4j_ontology_loader.models.types import (
    FinancialInstrument as FI,
    Currency,
    Date,
    Price,
    InterestRate,
    Shorttext,
    Longtext,
    FinancialInstrumentIdentification,
    CfiCode,
)


def property_relationship_types() -> list[RelTypeDef]:
    rels: list[RelTypeDef] = []
    # FinancialInstrument general properties
    rels.append(extract_rel_type("HasName", FI, Longtext))
    rels.append(extract_rel_type("HasShortName", FI, Shorttext))
    rels.append(extract_rel_type("HasIdentification", FI, FinancialInstrumentIdentification))
    rels.append(extract_rel_type("HasCfiCode", FI, CfiCode))
    rels.append(extract_rel_type("CurrencyOfDenomination", FI, Currency))

    # Nested relations of type objects
    rels.append(extract_rel_type("PaymentDate", InterestRate, Date))
    rels.append(extract_rel_type("PriceCurrency", Price, Currency))

    return rels


"""
Bond-specific property relations and inheritance relations.

We avoid importing concrete model classes here (e.g., Bond, Equity, Option)
to prevent import-time dependency issues in tests. Instead, we construct
RelTypeDef entries directly using known labels and snake_case keys.
"""


def bond_property_relationship_types() -> list[RelTypeDef]:
    rels: list[RelTypeDef] = []
    # Embedded objects on Bond become relations to their node types
    rels.append(RelTypeDef(name="HasInterestRate", from_label="Bond", to_label="InterestRate", from_key="bond", to_key="interest_rate"))
    rels.append(RelTypeDef(name="HasMaturityDate", from_label="Bond", to_label="Date", from_key="bond", to_key="date"))
    rels.append(RelTypeDef(name="HasIssueDate", from_label="Bond", to_label="Date", from_key="bond", to_key="date"))
    rels.append(RelTypeDef(name="HasConversionPrice", from_label="Bond", to_label="Price", from_key="bond", to_key="price"))
    # Reuse the generic name for currency of denomination
    rels.append(RelTypeDef(name="CurrencyOfDenomination", from_label="Bond", to_label="Currency", from_key="bond", to_key="currency"))
    # Underlying instrument relation to abstract FinancialInstrument
    rels.append(RelTypeDef(name="UnderlyingInstrument", from_label="Bond", to_label="FinancialInstrument", from_key="bond", to_key="financial_instrument"))
    return rels


def inheritance_relationship_types() -> list[RelTypeDef]:
    """Ontology-level inheritance (schema) relations between concrete subtypes and FinancialInstrument."""
    rels: list[RelTypeDef] = []
    rels.append(RelTypeDef(name="IsA", from_label="Bond", to_label="FinancialInstrument", from_key="bond", to_key="financial_instrument"))
    rels.append(RelTypeDef(name="IsA", from_label="Equity", to_label="FinancialInstrument", from_key="equity", to_key="financial_instrument"))
    rels.append(RelTypeDef(name="IsA", from_label="Option", to_label="FinancialInstrument", from_key="option", to_key="financial_instrument"))
    return rels
