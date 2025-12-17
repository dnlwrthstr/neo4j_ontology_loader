from pydantic import BaseModel, Field

class TradingVenue(BaseModel):
    id: str = Field(..., description="Unique identifier for the trading venue", json_schema_extra={"unique": True})
    legal_name: str
