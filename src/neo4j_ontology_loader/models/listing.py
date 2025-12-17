from pydantic import BaseModel,Field

class Listing(BaseModel):
    id: str = Field(..., description="Unique identifier for the listing", json_schema_extra={"unique": True})
    ticker: str
    trading_place_id: str = Field(..., description="Unique identifier for the trading venue")
    instrument_id: str = Field(..., description="Unique identifier for the instriment type")
    trading_currency: str
    main: bool = False
    main_for_trading_currency: bool = False

# Market Data
    min_lot_amount: str | None
    round_lot_amount:  str | None
    interest_calculation_type:  str | None
    pricing_notation_type:  str | None
    pricing_factor: str | None
    dividend_yield: str | None