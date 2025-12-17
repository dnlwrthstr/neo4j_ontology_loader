from pydantic import BaseModel, Field


class CrossCurrencyRate(BaseModel):
    currency: str = Field(..., description="Currency code (e.g., CHF, USD, OPL)")
    cross_rate: float = Field(..., description="Cross rate value against base (likely CHF)")
    date: str = Field(..., description="Timestamp of the rate in ISO-8601")
