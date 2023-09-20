from datetime import datetime, timedelta
from settings import *
from jose import JWTError, jwt

async def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

from jose import JWTError, jwt
from typing import Optional

async def decode_access_token(token: str, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM) -> Optional[dict]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError:
        return None
