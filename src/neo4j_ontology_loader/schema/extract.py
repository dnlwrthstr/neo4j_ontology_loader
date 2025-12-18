from pydantic import BaseModel
from neo4j_ontology_loader.schema.types import EntityDef, PropertyDef, RelTypeDef, ComplexPropertiesDef
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

def extract_node_type(model: type[BaseModel], *, abstract: bool = False) -> EntityDef:
    # Abstract nodes are markers only; they must not expose properties in the schema
    if abstract:
        return EntityDef(name=model.__name__, key=infer_key(model), properties=[], abstract=True)
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
    return EntityDef(name=model.__name__, key=infer_key(model), properties=props, abstract=False)


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
    # Only include relationships that do not involve abstract marker nodes.
    # Abstract nodes (e.g., FinancialInstrument) are used exclusively for IsA relations.
    return [
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
    # Only nested relations of type objects. Abstract marker nodes carry no properties.
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


# ------------------- ObjectProperty support -------------------

from typing import get_origin, get_args, Optional as TypingOptional
import inspect
import neo4j_ontology_loader.models.types as model_types


def _is_basic_type(annotation: object) -> bool:
    """Return True if the annotation represents a basic scalar type (str, int, float, bool) possibly Optional.

    This is used to decide which fields become simple properties on ObjectProperty nodes versus
    nested ObjectProperty relationships.
    """
    basic = {str, int, float, bool}
    origin = get_origin(annotation)
    if origin is None:
        return annotation in basic
    if origin is TypingOptional or origin is list or origin is tuple or origin is set:
        # unwrap Optional[T]
        args = [a for a in get_args(annotation) if a is not type(None)]  # noqa: E721
        return len(args) == 1 and args[0] in basic
    # Other typing constructs considered non-basic here
    return False


def _is_object_property_model(obj: object) -> bool:
    return (
        inspect.isclass(obj)
        and issubclass(obj, BaseModel)
        and obj.__name__ != "FinancialInstrument"
    )


def discover_object_property_models() -> list[type[BaseModel]]:
    """Discover embedded object property models defined in models/types.py.

    We treat all Pydantic BaseModel classes in models/types.py, except abstract markers,
    as ObjectProperty node candidates.
    """
    models: list[type[BaseModel]] = []
    for _, obj in vars(model_types).items():
        if _is_object_property_model(obj):
            models.append(obj)
    return models


def extract_object_property_node(model: type[BaseModel]) -> ComplexPropertiesDef:
    props: list[PropertyDef] = []
    for name, field in model.model_fields.items():
        ann = field.annotation
        if _is_basic_type(ann):
            extra = field.json_schema_extra or {}
            t = getattr(ann, "__name__", str(ann))
            props.append(
                PropertyDef(
                    name=name,
                    type=t,
                    required=field.is_required(),
                    unique=bool(extra.get("unique", False)),
                )
            )
        # else: nested object property, expressed via relationships
    return ComplexPropertiesDef(name=model.__name__, key=infer_key(model), properties=props)


def complex_properties_node_types() -> list[ComplexPropertiesDef]:
    return [extract_object_property_node(m) for m in discover_object_property_models()]


def complex_properties_relationship_types() -> list[RelTypeDef]:
    """Relationships among ObjectProperty nodes derived from nested fields."""
    rels: list[RelTypeDef] = []
    candidates = {m.__name__: m for m in discover_object_property_models()}
    for model in candidates.values():
        for fname, field in model.model_fields.items():
            ann = field.annotation
            # Unwrap Optional[T]
            origin = get_origin(ann)
            if origin is TypingOptional:
                args = [a for a in get_args(ann) if a is not type(None)]  # noqa: E721
                if args:
                    ann = args[0]
                    origin = get_origin(ann)
            if inspect.isclass(ann) and issubclass(ann, BaseModel) and ann.__name__ in candidates:
                # Create a relationship from model to ann using a deterministic name
                rel_name = f"{model.__name__}{fname[0].upper()}{fname[1:]}"
                rels.append(
                    RelTypeDef(
                        name=rel_name,
                        from_label=model.__name__,
                        to_label=ann.__name__,
                        from_key=infer_key(model),
                        to_key=infer_key(ann),
                    )
                )
    return rels
