from __future__ import annotations

from enum import Enum
from typing import Literal, Optional, List

from pydantic import BaseModel, Field


class OptionType(Enum):
    CALL = 'call'
    PUT = 'put'


class OptionStyle(Enum):
    AMERICAN = 'american'
    EUROPEAN = 'european'
    BERMUDAN = 'bermudan'
    ASIAN = 'asian'


class DayCountBasis(Enum):
    ACT_360 = 'act_360'
    ACT_365 = 'act_365'
    ACT_ACTICMA = 'act_actIcma'
    ACT_ACTISDA = 'act_actIsda'
    ACT_ACTAFB = 'act_actAfb'
    ACT_365L = 'act_365L'
    BUS_252 = 'bus_252'
    U30_360 = 'u30_360'
    U30E_360ICMA = 'u30E_360Icma'
    U30E_360ISDA = 'u30E_360Isda'
    U30E_360 = 'u30E_360'
    U30U_360 = 'u30U_360'


class FinancialInstrumentType(Enum):
    CASH = 'cash'
    BOND = 'bond'
    EQUITY = 'equity'
    FUND = 'fund'
    INDEX = 'index'
    COMMODITY = 'commodity'
    OPTION = 'option'
    FUTURE = 'future'
    FXFORWARD = 'fxForward'
    FXSWAP = 'fxSwap'
    FXOPTION = 'fxOption'
    MORTGAGE = 'mortgage'
    CREDIT = 'credit'
    FIXEDLOAN = 'fixedLoan'
    FIXEDDEPOSIT = 'fixedDeposit'
    CALLABLELOAN = 'callableLoan'
    CALLABLEDEPOSIT = 'callableDeposit'
    INTERESTRATESWAP = 'interestRateSwap'
    TOTALRETURNSWAP = 'totalReturnSwap'
    CREDITDEFAULTSWAP = 'creditDefaultSwap'
    CRYPTOASSET = 'cryptoAsset'
    OTHER = 'other'


class Currency(BaseModel):
    value: str = Field(..., description='ISO 4217 currency code.')


class Date(BaseModel):
    value: str = Field(..., description='Date according to ISO 8601 (YYYY-MM-DD).')


class DateTime(BaseModel):
    value: str = Field(..., description='DateTime according to ISO 8601.')


class ContractSize(BaseModel):
    value: float = Field(..., description='Contract size of an instrument.')


class Price(BaseModel):
    type: Literal['actual', 'percentage'] = Field(...,
                                                  description='Indicates whether the price is an actual currency amount per unit or a percentage.\n')
    value: float = Field(..., description='Signed decimal price value.')
    currency: Optional[Currency] = Field(None, description='Currency of the price, if applicable.')


class CurrencyAmount(BaseModel):
    amount: float = Field(..., description='Signed amount.')
    currency: Currency = Field(..., description='Currency of the amount.')


class InterestRate(BaseModel):
    type: Literal['fixed', 'variable', 'staggered'] = Field(...,
                                                            description='Type of interest: - fixed: fixed interest rate - variable: floating rate based on a benchmark - staggered: rate set at different levels for different periods\n')
    value: Optional[float] = Field(None, description='Current rate as decimal (e.g. 0.00125).')
    dayCountBasis: Optional[DayCountBasis] = Field(None, description='Day count basis for interest calculation.')
    paymentDate: Optional[Date] = Field(None, description='Date of the next interest payment.')
    paymentFrequency: Optional[
        Literal['annual', 'monthly', 'quarterly', 'semiAnnual', 'weekly', 'atMaturity', 'other']] = Field(None,
                                                                                                          description='Frequency of interest payments.')
    basis: Optional[str] = Field(None, description='Benchmark rate used for floating interest (e.g. LIBOR, EURIBOR).\n')
    spread: Optional[float] = Field(None, description='Spread added to the base rate (basis) for floating rates.\n')


class FinancialInstrumentIdentification(BaseModel):
    identifier: str = Field(..., description='Instrument identification string.')
    type: Literal[
        'isin', 'sedol', 'cusip', 'ric', 'tickerSymbol', 'bloomberg', 'cta', 'quick', 'wertpapier', 'dutch', 'valoren', 'sicovam', 'belgian', 'common', 'iso3', 'otherProprietaryIdentification'] = Field(
        ..., description='Type of instrument identifier (ISIN preferred, but other schemes are possible).\n')


class Shorttext(BaseModel):
    language: Literal['en', 'de', 'fr', 'it'] = Field(..., description='Language of the short name.')
    value: str = Field(..., description='Short text in the specified language.')


class Longtext(BaseModel):
    language: Literal['en', 'de', 'fr', 'it'] = Field(..., description='Language of the long name.')
    value: str = Field(..., description='Long narrative text in the specified language.')


class CfiCode(BaseModel):
    value: str = Field(...,
                       description='Classification of financial instrument (CFI) code according to ISO 10962. At least the CFI Category (1st char) and Group (2nd char) must be present.\n')


class FinancialInstrument(BaseModel):
    type: FinancialInstrumentType = Field(..., description='Type discriminator for the financial instrument.')
    name: Longtext = Field(..., description='Name of the financial instrument in free text.')
    shortName: Optional[Shorttext] = Field(None, description='Short name of the financial instrument.')
    identificationList: Optional[List[FinancialInstrumentIdentification]] = Field(None,
                                                                                  description='List of instrument identifications.')
    cfiCode: Optional[CfiCode] = Field(None, description='CFI classification code of the instrument.')
    currencyOfDenomination: Optional[Currency] = Field(None,
                                                       description='Currency in which the instrument is denominated.')
    hasFactor: Optional[bool] = Field(None,
                                      description='Indicates if there is a factor present for this financial instrument. TRUE with missing factor may mean data is unavailable.\n')
    factor: Optional[float] = Field(None, description='Factor value for the instrument (e.g. split factor).')
    additionalDetails: Optional[str] = Field(None, description='Additional narrative information about the instrument.')


# ---- Equity-specific embedded types ----

class DividendPolicy(BaseModel):
    frequency: Optional[Literal['annual', 'semiAnnual', 'quarterly', 'monthly', 'irregular']] = Field(
        None, description='Typical frequency of dividend payments.'
    )
    lastDividendDate: Optional[Date] = Field(None, description='Date of the most recent dividend payment.')
    dividendPerShare: Optional[CurrencyAmount] = Field(
        None, description='Most recent dividend per share amount.'
    )
    payoutRatio: Optional[float] = Field(
        None, description='Payout ratio as decimal (e.g. 0.45 for 45%).'
    )


class KeyFigures(BaseModel):
    marketCap: Optional[CurrencyAmount] = Field(None, description='Market capitalization.')
    sharesOutstanding: Optional[float] = Field(None, description='Number of shares outstanding.')
    eps: Optional[float] = Field(None, description='Earnings per share.')
    peRatio: Optional[float] = Field(None, description='Price-to-earnings ratio.')
    roe: Optional[float] = Field(None, description='Return on equity as decimal.')
