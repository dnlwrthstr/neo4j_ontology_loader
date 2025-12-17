from pydantic import BaseModel


# Instrument -> Issuer
class IssuedBy(BaseModel):
    # Instrument (from) identified by its id (primary key)
    source_id: str
    # Issuer (to) identified by its LEI
    target_lei: str


# Instrument -> Ultimate Issuer
class UltimatelyIssuedBy(BaseModel):
    source_id: str
    target_lei: str


# Instrument -> InstrumentType
class HasType(BaseModel):
    # Instrument (from) identified by its id (primary key)
    source_id: str
    # InstrumentType (to) identified by its id
    target_id: str


# Instrument -> TradingVenue (main trading place)
class MainTradingPlace(BaseModel):
    # Instrument (from) identified by its id (primary key)
    source_id: str
    # TradingVenue (to) identified by its id
    target_id: str


# Listing -> Instrument
class ListingOfInstrument(BaseModel):
    # Listing (from) identified by its id
    source_id: str
    # FinancialInstrument (to) identified by its id
    target_id: str


# Listing -> TradingVenue
class ListedOn(BaseModel):
    # Listing (from) identified by its id
    source_id: str
    # TradingVenue (to) identified by its id
    target_id: str


# Quote -> Listing
class QuoteOfListing(BaseModel):
    # Quote (from) identified by its natural key composed by listing_id and quote_date
    # We use listing_id + quote_date when creating relationships, but for schema purposes
    # we reference by listing_id here as the minimal pointer
    source_listing_id: str
    # Listing (to) identified by its id
    target_id: str
