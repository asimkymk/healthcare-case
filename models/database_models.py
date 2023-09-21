from datetime import datetime
from sqlalchemy import ForeignKey, create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pyodbc
from settings import *


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'
    Id = Column(Integer, primary_key=True, index=True)
    Username = Column(String(255), unique=True)
    Password = Column(String(255))
    CreatedAt = Column(DateTime, default=datetime.now)
    tokens = relationship("Token", back_populates="user")

class Customer(Base):
    __tablename__ = 'Customers'
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String(255))
    Surname = Column(String(255))
    Gsm = Column(String(20), unique=True)
    Gender = Column(String(10))
    Birthday = Column(DateTime)
    CreatedAt = Column(DateTime, default=datetime.now)
    purchases = relationship("Purchase", back_populates="customer")

class Token(Base):
    __tablename__ = 'Tokens'
    Id = Column(Integer, primary_key=True, index=True)
    UserId = Column(Integer, ForeignKey('Users.Id'))
    Token = Column(String(255), unique=True)
    ExpiresAt = Column(DateTime)
    CreatedAt = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="tokens")

class Purchase(Base):
    __tablename__ = 'Purchases'
    Id = Column(Integer, primary_key=True, index=True)
    CustomerId = Column(Integer, ForeignKey('Customers.Id'))
    PurchaseDate = Column(DateTime)
    ListingPrice = Column(Float(10))
    SalePrice = Column(Float(10))
    DiscountPercentage = Column(Float(5))
    CreatedAt = Column(DateTime, default=datetime.now)
    customer = relationship("Customer", back_populates="purchases")
