from fastapi import FastAPI, HTTPException, Depends, Security
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import database_models
from database_models import SessionLocal, User, Token, Customer
from fastapi.security import OAuth2PasswordBearer
from core.password_generator import hash_password, verify_password
from core.tokenizer import *
from settings import *
from models.request_models import *
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.exceptions import RequestValidationError
app = FastAPI()

# Şifreleme için
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        content=exc.detail,
        status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        content={"success": False, "unsuccess_reason": "Unexpected request!"},
        status_code=400
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token",auto_error=False)

async def get_current_user(token: str = Security(oauth2_scheme), db: Session = Depends(get_db), request: Request = None):
    if not token:
        raise HTTPException(status_code=401, detail={"success": False, "unsuccess_reason": "Not authenticated."})

    try:
        payload = await decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail={"success": False, "unsuccess_reason": "Invalid token.1"})


    if payload is None:
        raise HTTPException(status_code=401, detail={"success": False, "unsuccess_reason": "Invalid token.2"})

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail={"success": False, "unsuccess_reason": "Invalid token.2"})

    token_data = db.query(Token).filter(Token.Token == token).first()
    if token_data is None:
        raise HTTPException(status_code=401, detail={"success": False, "unsuccess_reason": "Token not found."})

    if token_data.ExpiresAt < datetime.utcnow():
        raise HTTPException(status_code=401, detail={"success": False, "unsuccess_reason": "Token has expired."})

    return username



@app.post("/user_login/", response_model=dict)
async def user_login(userLogin:UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.Username == userLogin.username).first()  # Changed to username
        if not user:
            return {"success": False, "unsuccess_reason": "Kullanıcı bulunamadı"}

        if not await verify_password(userLogin.password, user.Password):  # Changed to password
            return {"success": False, "unsuccess_reason": "Yanlış şifre"}

        access_token = await create_access_token(data={"sub": userLogin.password})  # Changed to username
        expires_at = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        db_token = Token(UserId=user.Id, Token=access_token, ExpiresAt=expires_at, CreatedAt=datetime.now())
        db.add(db_token)
        db.commit()

        return {"success": True, "unsuccess_reason": "", "access_token": access_token}
    except:
        return {"success": False, "unsuccess_reason": ""}

@app.post("/create_customer/", response_model=dict)
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    existing_customer = db.query(Customer).filter(Customer.Gsm == customer.gsm).first()
    if existing_customer:
        return {"success": False, "unsuccess_reason": "Bu GSM numarası zaten kayıtlı"}
    
    db_customer = Customer(
        Name=customer.name,
        Surname=customer.surname,
        Gsm=customer.gsm
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)

    return {"success": True, "unsuccess_reason": "", "customer_id": db_customer.Id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
