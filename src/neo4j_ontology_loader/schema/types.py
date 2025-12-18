from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class PropertyDef:
    name: str
    type: str
    required: bool
    unique: bool

@dataclass(frozen=True)
class ComplexPropertiesDef:
    """Schema definition for an ObjectProperty node type.

    ObjectProperty nodes represent embedded objects from domain models. They can
    have simple properties (basic types) and/or nested ObjectProperty links.
    """
    name: str
    key: str
    properties: list[PropertyDef]

@dataclass(frozen=True)
class EntityDef:
    name: str
    key: str
    properties: list[PropertyDef]
    # When abstract=True, the type represents an abstract concept (no data nodes)
    # and should not produce database constraints for its properties.
    abstract: bool = False

@dataclass(frozen=True)
class RelTypeDef:
    name: str
    from_label: str
    to_label: str
    from_key: str
    to_key: str

    def __iter__(self):
        # convenience unpacking (name, from_label, to_label, from_key, to_key)
        return iter((self.name, self.from_label, self.to_label, self.from_key, self.to_key))
