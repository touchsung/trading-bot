from enum import Enum
from pydantic import BaseModel
from database.model import SideType


class PriceTypeEnum(str, Enum):
    Limit = "Limit"
    ATO = "ATO"
    MPMTL = "MP-MTL"
    MPMKT = "MP-MKT"


class ValidityTypeEnum(str, Enum):
    Day = "Day"
    FOK = "FOK"
    IOC = "IOC"
    Date = "Date"
    Cancel = "Cancel"


class MarketPhase(Enum):
    MarketOpen = "Market Open"
    PreClose = "Pre-Close"
    MarketClose = "Market Close"
    OutOfWorkingHours = "Out of working hours"
    PreOpen = "Pre-Open"


class PlaceOrder(BaseModel):
    account_no: str
    symbol: str
    side: SideType
    price_type: PriceTypeEnum = PriceTypeEnum.Limit
    price: float
    validity_type: ValidityTypeEnum = ValidityTypeEnum.Day
    volume: float
