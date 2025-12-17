from pydantic import BaseModel, Field

class Issuer(BaseModel):
    lei: str = Field(..., description="Legal Entity Identifier", json_schema_extra={"unique": True})
    legal_name: str
