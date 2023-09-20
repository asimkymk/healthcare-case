from pydantic import BaseModel

class UserLogin(BaseModel):
    username: str
    password: str

class CustomerCreate(BaseModel):
    name: str
    surname: str
    gsm: str