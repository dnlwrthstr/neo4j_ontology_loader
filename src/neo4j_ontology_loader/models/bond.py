from typing import Optional

from neo4j_ontology_loader.models.types import (
    FinancialInstrument,
    InterestRate,
    Price,
    Date,
    Currency
)
from pydantic import Field


class Bond(FinancialInstrument):
    interestRate: Optional[InterestRate] = Field(None, description='Interest rate definition.')
    maturityDate: Optional[Date] = Field(None, description='Bond maturity date.')
    issueDate: Optional[Date] = Field(None, description='Issue date of the bond.')
    conversionPrice: Optional[Price] = Field(None, description='Conversion price if bond is convertible.')
    currencyOfDenomination: Optional[Currency] = Field(None, description='Currency in which the bond is denominated.')
    minimumDenomination: Optional[float] = Field(None, description='Minimum denomination allowed for trading.')
    minimumIncrement: Optional[float] = Field(None, description='Minimum tradable increment.')
    underlyingFinancialInstrument: Optional[FinancialInstrument] = Field(None,
                                                                         description='Underlying financial instrument for structured / convertible bonds.')
