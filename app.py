from fastapi import FastAPI, HTTPException, Depends, Security
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import database_models
from database_models import SessionLocal, User, Token, Customer, Purchase
from fastapi.security import OAuth2PasswordBearer
from core.password_generator import hash_password, verify_password
from core.tokenizer import *
from settings import *
from models.request_models import *
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.exceptions import RequestValidationError
import pandas as pd
import base64
from io import BytesIO


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
        raise HTTPException(status_code=401, detail={"success": False, "unsuccess_reason": "Invalid token."})


    if payload is None:
        raise HTTPException(status_code=401, detail={"success": False, "unsuccess_reason": "Invalid token."})

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail={"success": False, "unsuccess_reason": "Invalid token."})

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
            return {"success": False, "unsuccess_reason": "User could not found!"}

        if not await verify_password(userLogin.password, user.Password):  # Changed to password
            return {"success": False, "unsuccess_reason": "Wrong password!"}

        access_token = await create_access_token(data={"sub": userLogin.password})  # Changed to username
        expires_at = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        db_token = Token(UserId=user.Id, Token=access_token, ExpiresAt=expires_at, CreatedAt=datetime.now())
        db.add(db_token)
        db.commit()

        return {"success": True, "unsuccess_reason": "", "access_token": access_token}
    except:
        return {"success": False, "unsuccess_reason": "Database error!"}

@app.post("/create_customer/", response_model=dict)
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        existing_customer = db.query(Customer).filter(Customer.Gsm == customer.gsm).first()
        if existing_customer:
            return {"success": False, "unsuccess_reason": "This GSM has already signed up!"}
        
        db_customer = Customer(
            Name=customer.name,
            Surname=customer.surname,
            Gsm=customer.gsm,
            Birthday=customer.birthDay,  # Optional
            Gender=customer.gender  # Optional
        )
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)

        return {"success": True, "unsuccess_reason": "", "customer_id": db_customer.Id}
    except:
        return {"success": False, "unsuccess_reason": "Database error!"}
    

@app.post("/create_purchase/", response_model=dict)
async def create_purchase(purchase: PurchaseCreate, username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        customer = db.query(Customer).filter(Customer.Id == purchase.customerId).first()
        if not customer:
            return {"success": False, "unsuccess_reason": "Customer not found"}

        discount_percentage = 0
        if purchase.salePrice < purchase.listingPrice:
            discount_percentage = ((purchase.listingPrice - purchase.salePrice) / purchase.listingPrice) * 100

        new_purchase = Purchase(
            CustomerId=purchase.customerId,
            PurchaseDate=purchase.purchaseDate,
            ListingPrice=purchase.listingPrice,
            SalePrice=purchase.salePrice,
            DiscountPercentage=discount_percentage
        )

        db.add(new_purchase)
        db.commit()
        db.refresh(new_purchase)

        return {"success": True, "unsuccess_reason": "", "purchase_id": new_purchase.Id}
    except:
        return {"success": False, "unsuccess_reason": "Database error!"}

@app.put("/update_customer/{customer_id}", response_model=dict)
async def update_customer(customer_id: int, customer: CustomerUpdate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        db_customer = db.query(Customer).filter(Customer.Id == customer_id).first()
        
        if not db_customer:
            return {"success": False, "unsuccess_reason": "Customer not found!"}
        
        if customer.name:
            db_customer.Name = customer.name
        if customer.surname:
            db_customer.Surname = customer.surname
        if customer.gsm:
            db_customer.Gsm = customer.gsm
        if customer.birthDay:
            db_customer.Birthday = customer.birthDay
        if customer.gender:
            db_customer.Gender = customer.gender
        
        db.commit()
        db.refresh(db_customer)
        
        return {"success": True, "unsuccess_reason": "", "customer_id": db_customer.Id}
    except:
        return {"success": False, "unsuccess_reason": "Database error!"}

@app.post("/purchase_summary/", response_model=dict)
async def purchase_summary(dates: DateRange, username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    try:

        purchases = db.query(Purchase).filter(Purchase.PurchaseDate >= dates.beginningDate, Purchase.PurchaseDate <= dates.endingDate).all()
    except:
        return {"success": False, "unsuccess_reason": "Database error!"}
    
    if not purchases:
        return {"success": False, "unsuccess_reason": "No purchases found in the given date range"}
    
    total_purchases = len(purchases)
    unique_customers = len(set([p.CustomerId for p in purchases]))
    total_revenue = sum([p.SalePrice for p in purchases])
    total_discount = sum([p.ListingPrice - p.SalePrice for p in purchases])
    
    try:

        df = pd.DataFrame([{
            "Customer Id": p.CustomerId,
            "Customer Birthday": db.query(Customer).filter(Customer.Id == p.CustomerId).first().Birthday,
            "Customer Gender": db.query(Customer).filter(Customer.Id == p.CustomerId).first().Gender,
            "Purchase Date": p.PurchaseDate,
            "Listing Price": p.ListingPrice,
            "Sale Price": p.SalePrice,
            "Discount Amount": p.ListingPrice - p.SalePrice,
            "Discount Percentage": p.DiscountPercentage
        } for p in purchases])
    except:
        return {"success": False, "unsuccess_reason": "Excel file could not created!"}
    
    df.sort_values("Purchase Date", inplace=True)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    output.seek(0)
    base64_excel = base64.b64encode(output.read()).decode("utf-8")
    
    return {
        "success": True,
        "unsuccess_reason": "",
        "total_purchases": total_purchases,
        "unique_customers": unique_customers,
        "total_revenue": total_revenue,
        "total_discount": total_discount,
        "base64_excel": base64_excel
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
