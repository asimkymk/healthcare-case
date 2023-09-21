from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserLogin(BaseModel):
    username: str
    password: str

class CustomerCreate(BaseModel):
    name: str
    surname: str
    gsm: str
    birthDay: Optional[datetime] = None
    gender: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    gsm: Optional[str] = None
    birthDay: Optional[datetime] = None
    gender: Optional[str] = None

class PurchaseCreate(BaseModel):
    customerId: int
    purchaseDate: datetime
    listingPrice: float
    salePrice: float

class DateRange(BaseModel):
    beginningDate: datetime
    endingDate: datetime

