import typer
import pandas as pd

from neo4j_ontology_loader.neo4j.driver import create_driver
from neo4j_ontology_loader.schema.extract import (
    extract_node_type,
    all_relationship_types,
    property_relationship_types,
    bond_property_relationship_types,
    inheritance_relationship_types,
)
from neo4j_ontology_loader.schema.ddl import constraint_cypher
from neo4j_ontology_loader.schema.persist import persist_schema, persist_relationship_types
from neo4j_ontology_loader.schema.ddl_apply import apply_cypher_statements
from neo4j_ontology_loader.schema.ddl_maintenance import (
    clean_database as clean_database_maintenance,
)
from neo4j_ontology_loader.schema.ddl_szkb import szkb_loading_indexes
from neo4j_ontology_loader.schema.types import NodeTypeDef, PropertyDef

from neo4j_ontology_loader.models.issuer import Issuer
from neo4j_ontology_loader.models.instrument_type import InstrumentType
from neo4j_ontology_loader.models.trading_venue import TradingVenue
from neo4j_ontology_loader.models.listing import Listing
from neo4j_ontology_loader.models.cross_currency_rate import CrossCurrencyRate
from neo4j_ontology_loader.models.quotes import Quote
from neo4j_ontology_loader.models.types import (
    FinancialInstrument as FI,
    Currency,
    Date,
    DateTime,
    ContractSize,
    Price,
    CurrencyAmount,
    InterestRate,
    FinancialInstrumentIdentification,
    Shorttext,
    Longtext,
    CfiCode,
)
from neo4j_ontology_loader.models.equity import Equity
from neo4j_ontology_loader.models.option import Option

from neo4j_ontology_loader.ingest.nodes import ingest_nodes
from neo4j_ontology_loader.ingest.relationship import ingest_relationships
from neo4j_ontology_loader.ingest.pandas_io import df_to_rows
import os
from neo4j_ontology_loader.schema import build_rel_cypher_casted

app = typer.Typer()

@app.command()
def install_schema():
    driver = create_driver()
    try:
        # Add all entity models under models/ (excluding relationship-only models)
        for model in (
            Issuer,
            InstrumentType,
            TradingVenue,
            Listing,
            CrossCurrencyRate,
            Quote,
        ):
            node = extract_node_type(model)
            persist_schema(driver, node)
            apply_cypher_statements(driver, constraint_cypher(node))

        # Persist node types for type system (models/types.py)
        # FinancialInstrument is abstract: constraints are skipped and it represents a schema concept
        for model, is_abstract in (
            (Currency, False),
            (Date, False),
            (DateTime, False),
            (ContractSize, False),
            (Price, False),
            (CurrencyAmount, False),
            (InterestRate, False),
            (FinancialInstrumentIdentification, False),
            (Shorttext, False),
            (Longtext, False),
            (CfiCode, False),
            (FI, True),
        ):
            node = extract_node_type(model, abstract=is_abstract)
            persist_schema(driver, node)
            apply_cypher_statements(driver, constraint_cypher(node))

        # Bond model has nested complex fields and a currently incompatible import.
        # We only persist what we can reliably map from SZKB bonds.csv.
        bond_node = NodeTypeDef(
            name="Bond",
            key="bond",
            properties=[
                PropertyDef(name="id", type="str", required=True, unique=True),
                PropertyDef(name="isin", type="str", required=False, unique=True),
                PropertyDef(name="name", type="str", required=False, unique=False),
                PropertyDef(name="short_name", type="str", required=False, unique=False),
                PropertyDef(name="currency_of_denomination", type="str", required=False, unique=False),
                PropertyDef(name="denomination", type="float", required=False, unique=False),
                PropertyDef(name="nominal_amount", type="float", required=False, unique=False),
                PropertyDef(name="issuer_id", type="str", required=False, unique=False),
                PropertyDef(name="interest_type", type="str", required=False, unique=False),
                PropertyDef(name="interest_rate", type="float", required=False, unique=False),
                PropertyDef(name="interest_payment_frequency", type="str", required=False, unique=False),
                PropertyDef(name="maturity_date", type="str", required=False, unique=False),
                PropertyDef(name="last_coupon_date", type="str", required=False, unique=False),
                PropertyDef(name="is_callable", type="bool", required=False, unique=False),
                PropertyDef(name="underlying_id", type="str", required=False, unique=False),
                PropertyDef(name="conversion_price_value", type="float", required=False, unique=False),
                PropertyDef(name="conversion_price_currency", type="str", required=False, unique=False),
            ],
        )
        persist_schema(driver, bond_node)
        apply_cypher_statements(driver, constraint_cypher(bond_node))
        # Persist relationship type definitions in ontology graph
        # Core relationships among primary entities
        persist_relationship_types(driver, all_relationship_types())
        # Property-as-relationship definitions for type system
        persist_relationship_types(driver, property_relationship_types())
        # Bond embedded objects become relations (schema-level)
        persist_relationship_types(driver, bond_property_relationship_types())
        # Inheritance relations from concrete subtypes to abstract FinancialInstrument
        persist_relationship_types(driver, inheritance_relationship_types())
        typer.echo("Schema installed (ontology persisted + constraints applied).")
    finally:
        driver.close()

@app.command()
def load_nodes(label: str, key: str, csv_path: str):
    driver = create_driver()
    try:
        df = pd.read_csv(csv_path)
        ingest_nodes(driver, label=label, key=key, rows=df_to_rows(df))
        typer.echo(f"Loaded nodes for label={label} from {csv_path}")
    finally:
        driver.close()

@app.command()
def load_szkb(base_dir: str = typer.Option(
    "data/szkb",
    help="Base directory containing SZKB CSV files",
)):
    """Load SZKB sample CSVs into the current database as nodes.

    Files expected in base_dir:
      - instrument_types.csv -> InstrumentType (key: id)
      - trading_venues.csv   -> TradingVenue   (key: id)
      - instruments.csv      -> Instrument     (key: id)
      - listings.csv         -> Listing        (key: id)
      - cross_rates.csv      -> CrossCurrencyRate (synthetic key: id=currency:date)
      - quotes.csv           -> Quote             (synthetic key: id=listing_id:quote_date)
    """
    driver = create_driver()
    try:
        def full(path: str) -> str:
            return os.path.join(base_dir, path)

        # Only persist properties that exist on the corresponding Pydantic models
        model_fields_by_label: dict[str, set[str]] = {
            "InstrumentType": set(InstrumentType.model_fields.keys()),
            "TradingVenue": set(TradingVenue.model_fields.keys()),
            "Listing": set(Listing.model_fields.keys()),
            "CrossCurrencyRate": set(CrossCurrencyRate.model_fields.keys()),
            "Quote": set(Quote.model_fields.keys()),
            # For Bond and Instrument we only keep the technical key 'id' (no CSV-derived attributes)
            "Bond": {"id"},
            "Instrument": {"id"},
        }

        def filter_props(label: str, rows: list[dict]) -> list[dict]:
            allowed = model_fields_by_label.get(label)
            if not allowed:
                return rows
            return [{k: v for k, v in r.items() if k in allowed} for r in rows]

        # 1) Instrument types
        path = full("instrument_types.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            typer.echo(f"Loading InstrumentType from {path} ...")
            rows = filter_props("InstrumentType", df_to_rows(df))
            ingest_nodes(driver, label="InstrumentType", key="id", rows=rows)
        else:
            typer.echo(f"Skipped: {path} not found")

        # 2) Trading venues
        path = full("trading_venues.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            typer.echo(f"Loading TradingVenue from {path} ...")
            rows = filter_props("TradingVenue", df_to_rows(df))
            ingest_nodes(driver, label="TradingVenue", key="id", rows=rows)
        else:
            typer.echo(f"Skipped: {path} not found")

        # 3) Instruments
        path = full("instruments.csv")
        if os.path.exists(path):
            df_instruments = pd.read_csv(path)
            # Only use `id` as upsert key; skip rows without a valid id
            before = len(df_instruments)
            df_instruments = df_instruments[df_instruments["id"].notna()]
            try:
                # also drop empty-string ids if any
                df_instruments = df_instruments[df_instruments["id"].astype(str).str.strip() != ""]
            except Exception:
                # If coercion fails, proceed with non-null filter only
                pass
            after = len(df_instruments)
            skipped = before - after
            typer.echo(f"Loading Instrument from {path} ...")
            if skipped:
                typer.echo(f"Skipped {skipped} Instrument rows without id")
            rows = filter_props("Instrument", df_to_rows(df_instruments))
            ingest_nodes(driver, label="Instrument", key="id", rows=rows)
        else:
            typer.echo(f"Skipped: {path} not found")

        # 4) Listings
        path = full("listings.csv")
        if os.path.exists(path):
            df_listings = pd.read_csv(path)
            typer.echo(f"Loading Listing from {path} ...")
            rows = filter_props("Listing", df_to_rows(df_listings))
            ingest_nodes(driver, label="Listing", key="id", rows=rows)
        else:
            typer.echo(f"Skipped: {path} not found")

        # 5) Cross currency rates (no natural single key -> synthetic id)
        path = full("cross_rates.csv")
        if os.path.exists(path):
            df_cross = pd.read_csv(path)
            if "currency" in df_cross.columns and "date" in df_cross.columns:
                df_cross["id"] = df_cross["currency"].astype(str) + ":" + df_cross["date"].astype(str)
            else:
                raise typer.BadParameter("cross_rates.csv must contain 'currency' and 'date' columns")
            typer.echo(f"Loading CrossCurrencyRate from {path} ...")
            # Do not persist synthetic id; keep only model-defined properties
            rows = filter_props("CrossCurrencyRate", df_to_rows(df_cross))
            ingest_nodes(driver, label="CrossCurrencyRate", key="id", rows=rows)
        else:
            typer.echo(f"Skipped: {path} not found")

        # 6) Bonds
        path = full("bonds.csv")
        if os.path.exists(path):
            df_bonds_raw = pd.read_csv(path)

            # Prepare mapping helpers
            def map_interest_type(v: str) -> str | None:
                s = str(v).strip().lower()
                if not s or s == 'nan':
                    return None
                if 'fixed' in s:
                    return 'fixed'
                if 'variable' in s or 'float' in s:
                    return 'variable'
                if 'stagger' in s:
                    return 'staggered'
                return s

            def map_freq(p: str) -> str | None:
                s = str(p).strip().upper()
                if not s or s == 'NAN':
                    return None
                return {
                    'P1Y': 'annual',
                    'P6M': 'semiAnnual',
                    'P3M': 'quarterly',
                    'P1M': 'monthly',
                }.get(s, 'other')

            # Build flat properties compatible with our persisted Bond schema
            def transform_row(r: dict) -> dict:
                def get(col: str):
                    return r.get(col, None)

                # Interest rate value in CSV is percentage (e.g., 4.375), convert to decimal
                rate_pct = get('actInterestRate')
                try:
                    rate_val = float(rate_pct) / 100.0 if pd.notna(rate_pct) else None
                except Exception:
                    rate_val = None

                # Conversion price
                conv_price = get('exercisePrice')
                try:
                    conv_price_val = float(conv_price) if pd.notna(conv_price) else None
                except Exception:
                    conv_price_val = None

                name_val = get('name@de') or get('shortName@de')

                return {
                    'id': get('id'),
                    'isin': get('isin'),
                    'name': name_val,
                    'short_name': get('shortName@de'),
                    'currency_of_denomination': get('nominalCurrency'),
                    'denomination': get('denomination'),
                    'nominal_amount': get('nominalAmount'),
                    'issuer_id': get('issuerId'),
                    'interest_type': map_interest_type(get('interestType')),
                    'interest_rate': rate_val,
                    'interest_payment_frequency': map_freq(get('payFreqPeriod')),
                    'maturity_date': get('maturityDate'),
                    'last_coupon_date': get('lastCouponDate'),
                    'is_callable': get('isCallable'),
                    'underlying_id': get('underlyingId'),
                    'conversion_price_value': conv_price_val,
                    'conversion_price_currency': get('exercisePriceCurr'),
                }

            # Filter out rows without an id, and transform
            rows: list[dict] = []
            before = len(df_bonds_raw)
            for r in df_bonds_raw.to_dict(orient='records'):
                if r.get('id') is None or str(r.get('id')).strip() == '':
                    continue
                rows.append(transform_row(r))
            after = len(rows)
            skipped = before - after
            typer.echo(f"Loading Bond from {path} ...")
            if skipped:
                typer.echo(f"Skipped {skipped} Bond rows without id")
            rows = filter_props("Bond", rows)
            ingest_nodes(driver, label="Bond", key="id", rows=rows)
        else:
            typer.echo(f"Skipped: {path} not found")

        # 7) Quotes (no natural single key -> synthetic id)
        path = full("quotes.csv")
        if os.path.exists(path):
            df_quotes = pd.read_csv(path)
            if "listing_id" in df_quotes.columns and "quote_date" in df_quotes.columns:
                df_quotes["id"] = df_quotes["listing_id"].astype(str) + ":" + df_quotes["quote_date"].astype(str)
            else:
                raise typer.BadParameter("quotes.csv must contain 'listing_id' and 'quote_date' columns")
            typer.echo(f"Loading Quote from {path} ...")
            # Do not persist synthetic id; keep only model-defined properties
            rows = filter_props("Quote", df_to_rows(df_quotes))
            ingest_nodes(driver, label="Quote", key="id", rows=rows)
        else:
            typer.echo(f"Skipped: {path} not found")

        # Relationships are model-driven only; no CSV-derived relationships are created here.
        typer.echo("SZKB CSVs loaded.")
    finally:
        driver.close()

@app.command()
def clean_database(
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Confirm cleanup without interactive prompt (drop all constraints/indexes and delete all nodes)",
    )
):
    """Drop all constraints and indexes, then delete all nodes and relationships.

    Warning: This operation is destructive and cannot be undone.
    """
    if not yes and not typer.confirm(
        "This will drop ALL constraints and indexes and delete ALL nodes/relationships. Continue?"
    ):
        typer.echo("Aborted.")
        return

    driver = create_driver()
    try:
        clean_database_maintenance(driver)
        typer.echo("Database cleaned: constraints and indexes dropped, all data removed.")
    finally:
        driver.close()


@app.command()
def install_szkb_ddl():
    """Install SZKB-specific non-unique indexes to speed up CSV loading."""
    driver = create_driver()
    try:
        apply_cypher_statements(driver, szkb_loading_indexes())
        typer.echo("SZKB DDL (indexes) installed.")
    finally:
        driver.close()

if __name__ == "__main__":
    app()
