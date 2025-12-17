from typing import Optional
from pydantic import Field


from neo4j_ontology_loader.models.types import (
    FinancialInstrument,
    Date,
    Price,
    ContractSize,
    OptionType,
    OptionStyle
)

class Option(FinancialInstrument):
    expiryDate: Optional[Date] = Field(None, description='Expiry date of the option.')
    exercisePrice: Optional[Price] = Field(None, description='Exercise (strike) price of the option.')
    contractSize: Optional[ContractSize] = Field(None, description='Contract size specifying standardized units.')
    optionType: Optional[OptionType] = Field(None, description='Type of option (call/put).')
    optionStyle: Optional[OptionStyle] = Field(None, description='Exercise style of the option (European/American/etc.).')
    underlyingFinancialInstrument: Optional[FinancialInstrument] = Field(None, description='The underlying financial instrument on which the option is written.')
