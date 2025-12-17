neo4j-ontology-loader
======================

Ontology‑driven Neo4j loader using Pydantic models and template‑based ingestion.

What you can do with the CLI:
- Persist the ontology schema and apply Neo4j constraints derived from Pydantic models
- Load nodes from CSV files into Neo4j (generic loader)
- Load the bundled SZKB sample dataset (nodes + relationships) in one go
- Clean a database (drop constraints/indexes and delete all data)


Quickstart
----------

Prerequisites:
- Python 3.11+
- Neo4j 5.x running and reachable (e.g., local Docker or remote instance)

1) Install

Use pip (editable for development or standard local install):

```
python -m venv .venv && source .venv/bin/activate
pip install -e .          # editable install for development
# or
pip install .             # standard install from the local checkout
```

2) Configure connection

The CLI reads connection details from environment variables. Defaults in parentheses.

Unix/macOS:
```
export NEO4J_URI="neo4j://localhost:7687"   # default
export NEO4J_USER="neo4j"                   # default
export NEO4J_PASSWORD="ontology"            # default
```

Windows (PowerShell):
```
$env:NEO4J_URI = "neo4j://localhost:7687"
$env:NEO4J_USER = "neo4j"
$env:NEO4J_PASSWORD = "ontology"
```

3) Install schema and constraints

This extracts the ontology from the Pydantic models, persists it, and applies node key constraints.

```
neo4j-ontology-loader install-schema
```

4) Load CSVs

Generic CSV loader:
```
neo4j-ontology-loader load-nodes <Label> <keyProperty> <path/to/file.csv>
```

Examples:
```
# Load InstrumentType by id
neo4j-ontology-loader load-nodes InstrumentType id ./data/szkb/instrument_types.csv

# Load TradingVenue by id
neo4j-ontology-loader load-nodes TradingVenue id ./data/szkb/trading_venues.csv
```

5) Load the SZKB sample dataset (optional)

This convenience command loads nodes and creates relationships derived from simple foreign keys.
```
neo4j-ontology-loader load-szkb --base-dir data/szkb
```

What it does:
- Loads nodes: InstrumentType(id), TradingVenue(id), Listing(id), CrossCurrencyRate(id), Quote(id), Bond(id)
- Synthetic ids:
  - CrossCurrencyRate.id = "<currency>:<date>"
  - Quote.id = "<listing_id>:<quote_date>"
- Creates relationships:
  - Listing -[ListedOn]-> TradingVenue (from Listing.trading_place_id)
  - Listing -[ListingOfInstrument]-> FinancialInstrument (from Listing.instrument_id)
  - FinancialInstrument -[HasType]-> InstrumentType (from instrument_type_id on the concrete subtype, if present)
  - FinancialInstrument -[MainTradingPlace]-> TradingVenue (from main_trading_place_id on the concrete subtype, if present)
  - Quote -[QuoteOfListing]-> Listing, where Listing.id is composite "<instrument_id>/<trading_place_id>"


CSV format notes
----------------

CSV headers must match the Pydantic model field names in `src/neo4j_ontology_loader/models`.
Examples:

- InstrumentType
  - required: `id`, `name`

- TradingVenue
  - required: `id`, `name`

- Bond
  - required: `id`, `isin`
  - optional: domain-specific fields (e.g., `interest_type`, `interest_rate`, `maturity_date`, etc.)

- Equity
  - required: `id`, `isin`
  - optional: dataset-specific attributes (e.g., `shortName@de`, etc.)

- Listing
  - required: `id` (composite like `instrument_id/trading_place_id`), `instrument_id`, `trading_place_id`

- CrossCurrencyRate
  - required columns: `currency`, `date` (a synthetic `id` is built as `currency:date`)

- Quote
  - required columns: `listing_id` (trading_place_id), `instrument_id`, `quote_date`
  - a synthetic `id` is built as `listing_id:quote_date`


CLI reference
-------------

```
# 1) Install ontology schema and apply constraints
neo4j-ontology-loader install-schema

# 2) Load nodes from a CSV (generic)
neo4j-ontology-loader load-nodes <Label> <keyProperty> <path/to/file.csv>

# 3) Load bundled SZKB sample dataset
neo4j-ontology-loader load-szkb [--base-dir data/szkb]

# 4) Clean the database (destructive!)
neo4j-ontology-loader clean-database [-y]
```

Warning: `clean-database` drops all constraints and non-lookup indexes and deletes all nodes/relationships. Use `-y` to skip the prompt.


Troubleshooting
---------------

- Authentication failed / wrong password
  - Ensure `NEO4J_PASSWORD` matches your database. The default in this tool is `ontology` if the env var is not set.
- Cannot connect
  - Check `NEO4J_URI` (bolt/neo4j scheme, host, port). For Neo4j Desktop/Docker, ensure the Bolt port (7687) is exposed and the DB is running.
- CSV headers don’t match
  - Column names must match model fields; see the models under `src/neo4j_ontology_loader/models` and notes above.
- Duplicate key errors on MERGE
  - Verify the chosen `<keyProperty>` truly identifies rows uniquely, and that your CSV has no duplicates for that key.
- Changing/adding models
  - Rerun `install-schema` to persist the updated ontology and constraints.


Notes
-----
- Ensure your virtual environment is activated so that the `neo4j-ontology-loader` console script is on your PATH.
- This project targets Neo4j 5.x and Python 3.11+.
- CSVs are read with pandas; large files may require additional memory.
