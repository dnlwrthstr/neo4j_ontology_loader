from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class RelSpec:
    rel_type: str
    from_label: str
    from_prop: str
    to_label: str
    to_prop: str
    # Name of the CSV source group: 'listings', 'instruments', 'quotes'
    source: str
    # Function that converts iterable of row dicts into iterable of
    # {'from_value': ..., 'to_value': ...} dicts for relationship creation
    build_rows: Callable[[Iterable[dict]], list[dict]]


def _rows_from_simple_columns(rows: Iterable[dict], from_col: str, to_col: str) -> list[dict]:
    out: list[dict] = []
    for r in rows:
        fv = str(r.get(from_col, "")).strip()
        tv = str(r.get(to_col, "")).strip()
        if fv and tv:
            out.append({"from_value": fv, "to_value": tv})
    return out


def _rows_quote_of_listing(rows: Iterable[dict]) -> list[dict]:
    # From: Quote.listing_id -> To: Listing.id composed as instrument_id/trading_place_id
    out: list[dict] = []
    for r in rows:
        market_id = str(r.get("listing_id", "")).strip()
        instr_id = str(r.get("instrument_id", "")).strip()
        quote_date = str(r.get("quote_date", "")).strip()
        if market_id and instr_id and quote_date:
            listing_composite_id = f"{instr_id}/{market_id}"
            out.append({"from_value": market_id, "to_value": listing_composite_id})
    return out


def get_szkb_relationship_specs() -> list[RelSpec]:
    return [
        RelSpec(
            rel_type="ListedOn",
            from_label="Listing", from_prop="id",
            to_label="TradingVenue", to_prop="id",
            source="listings",
            build_rows=lambda rows: _rows_from_simple_columns(rows, "id", "trading_place_id"),
        ),
        RelSpec(
            rel_type="ListingOfInstrument",
            from_label="Listing", from_prop="id",
            to_label="Instrument", to_prop="id",
            source="listings",
            build_rows=lambda rows: _rows_from_simple_columns(rows, "id", "instrument_id"),
        ),
        RelSpec(
            rel_type="HasType",
            from_label="Instrument", from_prop="id",
            to_label="InstrumentType", to_prop="id",
            source="instruments",
            build_rows=lambda rows: _rows_from_simple_columns(rows, "id", "instrument_type_id"),
        ),
        RelSpec(
            rel_type="MainTradingPlace",
            from_label="Instrument", from_prop="id",
            to_label="TradingVenue", to_prop="id",
            source="instruments",
            build_rows=lambda rows: _rows_from_simple_columns(rows, "id", "main_trading_place_id"),
        ),
        RelSpec(
            rel_type="QuoteOfListing",
            from_label="Quote", from_prop="listing_id",
            to_label="Listing", to_prop="id",
            source="quotes",
            build_rows=_rows_quote_of_listing,
        ),
    ]
