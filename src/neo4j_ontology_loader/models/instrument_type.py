from pydantic import BaseModel, Field, ConfigDict


class InstrumentType(BaseModel):
    id: str = Field(
        ..., description="Unique identifier for the instrument type", json_schema_extra={"unique": True}
    )
    name_de: str = ""
    sort_index_de: str = ""

    # Forbid extra keys to ensure only model-defined properties are stored
    model_config = ConfigDict(extra="forbid")
