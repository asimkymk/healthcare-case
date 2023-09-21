from fastapi import FastAPI, HTTPException, Depends, Security, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError
from datetime import datetime, timedelta
from models.database_models import SessionLocal, User, Token, Customer, Purchase
from fastapi.security import OAuth2PasswordBearer
from core.password_generator import verify_password
from core.tokenizer import create_access_token, decode_access_token
from settings import ACCESS_TOKEN_EXPIRE_MINUTES
from models.request_models import UserLogin, CustomerCreate, PurchaseCreate, CustomerUpdate, DateRange
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import pandas as pd
import base64
from io import BytesIO
from models.response_models import CustomHTTPException, ErrorResponse


app = FastAPI()

async def raise_http_exception(detail: str, status_code: int = 400):
    raise CustomHTTPException(status_code=status_code, detail=ErrorResponse(success=False, unsuccess_reason=detail))

@app.exception_handler(CustomHTTPException)
async def custom_exception_handler(request, exc: CustomHTTPException):
    return JSONResponse(
        content=exc.detail,
        status_code=exc.status_code
    )

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user(token: str = Security(oauth2_scheme), db: Session = Depends(get_db), request: Request = None):
    if not token:
        await raise_http_exception("Not authenticated.", 401)

    try:
        payload = await decode_access_token(token)
    except JWTError:
        await raise_http_exception("Invalid token.", 401)

    if payload is None:
        await raise_http_exception("Invalid token.", 401)
    try:

        username: str = payload.get("sub")
    except:
        await raise_http_exception("Token could not be resolved", 401)
    if username is None:
        await raise_http_exception("Token could not be resolved", 401)

    token_data = db.query(Token).filter(Token.Token == token).first()
    if token_data is None:
        await raise_http_exception("Token not found", 401)

    if token_data.ExpiresAt < datetime.utcnow():
        await raise_http_exception("Token has expired", 401)

    return username


# Kullanıcı işlemleri
@app.post("/user_login/", response_model=dict)
async def user_login(userLogin: UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.Username == userLogin.username).first()
        if not user:
            await raise_http_exception("User could not found!", 401)
        if not await verify_password(userLogin.password, user.Password):
            await raise_http_exception("Wrong password!", 401)
        
        access_token = await create_access_token(data={"sub": userLogin.password})
        expires_at = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        db_token = Token(UserId=user.Id, Token=access_token, ExpiresAt=expires_at, CreatedAt=datetime.now())
        db.add(db_token)
        db.commit()
        return {"success": True, "unsuccess_reason": "", "access_token": access_token}
    except HTTPException as e:
        raise e
    except:
        await raise_http_exception("Database error!")

@app.api_route("/user_login/", methods=["GET", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "CONNECT", "TRACE"])
async def catch_all_methods_for_user_login(request: Request):
    await raise_http_exception(f"Method {request.method} not allowed", 405)

# Müşteri işlemleri
@app.post("/create_customer/", response_model=dict)
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        existing_customer = db.query(Customer).filter(Customer.Gsm == customer.gsm).first()
        if existing_customer:
            await raise_http_exception(f"This GSM has already signed up!", 405)
        
        db_customer = Customer(
            Name=customer.name,
            Surname=customer.surname,
            Gsm=customer.gsm,
            Birthday=customer.birthDay,
            Gender=customer.gender
        )
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)

        return {"success": True, "unsuccess_reason": "", "customer_id": db_customer.Id}
    except CustomHTTPException as e:
        raise e
    except Exception as e:
        await raise_http_exception(f"Database error!", 500)


@app.api_route("/create_customer/", methods=["GET", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "CONNECT", "TRACE"])
async def catch_all_methods_for_user_login(request: Request):
    await raise_http_exception(f"Method {request.method} not allowed", 405)

@app.put("/update_customer/{customer_id}", response_model=dict)
async def update_customer(customer_id: int, customer: CustomerUpdate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        db_customer = db.query(Customer).filter(Customer.Id == customer_id).first()
        if not db_customer:
            await raise_http_exception("Customer not found!", 400)
        
        if customer.name: db_customer.Name = customer.name
        if customer.surname: db_customer.Surname = customer.surname
        if customer.gsm: db_customer.Gsm = customer.gsm
        if customer.birthDay: db_customer.Birthday = customer.birthDay
        if customer.gender: db_customer.Gender = customer.gender
        db.commit()
        db.refresh(db_customer)
        return {"success": True, "unsuccess_reason": "", "customer_id": db_customer.Id}
    except HTTPException as e:
        raise e
    except:
        await raise_http_exception("Database error!")

@app.api_route("/update_customer/", methods=["GET", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "CONNECT", "TRACE"])
async def catch_all_methods_for_user_login(request: Request):
    await raise_http_exception(f"Method {request.method} not allowed", 405)

# Alışveriş işlemleri
@app.post("/create_purchase/", response_model=dict)
async def create_purchase(purchase: PurchaseCreate, username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        customer = db.query(Customer).filter(Customer.Id == purchase.customerId).first()
        if not customer:
            await raise_http_exception("Customer not found", 400)
        
        discount_percentage = 0 if purchase.salePrice >= purchase.listingPrice else ((purchase.listingPrice - purchase.salePrice) / purchase.listingPrice) * 100
        new_purchase = Purchase(CustomerId=purchase.customerId, PurchaseDate=purchase.purchaseDate, ListingPrice=purchase.listingPrice, SalePrice=purchase.salePrice, DiscountPercentage=discount_percentage)
        db.add(new_purchase)
        db.commit()
        db.refresh(new_purchase)
        return {"success": True, "unsuccess_reason": "", "purchase_id": new_purchase.Id}
    except HTTPException as e:
        raise e
    except:
        await raise_http_exception("Database error!")

@app.api_route("/create_purchase/", methods=["GET", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "CONNECT", "TRACE"])
async def catch_all_methods_for_user_login(request: Request):
    await raise_http_exception(f"Method {request.method} not allowed", 405)


# Rapor işlemleri
@app.post("/purchase_summary/", response_model=dict)
async def purchase_summary(dates: DateRange, username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        purchases = db.query(Purchase).filter(Purchase.PurchaseDate >= dates.beginningDate, Purchase.PurchaseDate <= dates.endingDate).all()
        
        if not purchases:
            await raise_http_exception("No purchases found in the given date range", 400)
        
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
        
    except HTTPException as e:
        raise e
    except Exception as e:
        await raise_http_exception("Database error!")

@app.api_route("/purchase_summary/", methods=["GET", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "CONNECT", "TRACE"])
async def catch_all_methods_for_user_login(request: Request):
    await raise_http_exception(f"Method {request.method} not allowed", 405)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
