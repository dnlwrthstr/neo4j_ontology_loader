from pydantic import BaseModel, Field


class Quote(BaseModel):
    # A quote is always bound to a listing (which in turn references an instrument)
    instrument_id: str = Field(..., description="Instrument identifier this quote belongs to")
    listing_id: str = Field(..., description="Listing identifier this quote belongs to")
    quote: float = Field(..., description="Last price/quote value")
    quote_date: str = Field(..., description="Timestamp of the quote in ISO-8601")
