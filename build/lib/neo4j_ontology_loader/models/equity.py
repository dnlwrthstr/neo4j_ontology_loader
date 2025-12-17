from typing import Optional
from pydantic import Field


from neo4j_ontology_loader.models.types import (
    FinancialInstrument,
    DividendPolicy,
    KeyFigures
)

class Equity(FinancialInstrument):
    dividend_policy: Optional[DividendPolicy] = Field(None, description='Information about the dividend policy of the equity.')
    key_figures: Optional[KeyFigures] = Field(None, description='Key financial figures related to the equity.')
