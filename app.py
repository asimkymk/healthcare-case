from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)

# MySQL veritabanına bağlantı ayarları
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://sa:12341234@localhost/KocHealthcare'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Users(db.Model):
    __tablename__ = 'Users'
    Id = db.Column(db.Integer, primary_key=True, name='Id')
    Username = db.Column(db.String(50), unique=True, nullable=False, name='Username')
    Password = db.Column(db.String(100), nullable=False, name='Password')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow, name='CreatedAt')


class Customers(db.Model):
    __tablename__ = 'Customers'
    Id = db.Column(db.Integer, primary_key=True, name='Id')
    Name = db.Column(db.String(50), nullable=False, name='Name')
    Surname = db.Column(db.String(50), nullable=False, name='Surname')
    Gsm = db.Column(db.String(20), name='Gsm')
    Gender = db.Column(db.String(10), name='Gender')
    Birthday = db.Column(db.Date, name='Birthday')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow, name='CreatedAt')


class Tokens(db.Model):
    __tablename__ = 'Tokens'
    Id = db.Column(db.Integer, primary_key=True, name='Id')
    UserId = db.Column(db.Integer, db.ForeignKey('Users.Id'), nullable=False, name='UserId')
    Token = db.Column(db.String(255), nullable=False, name='Token')
    ExpiresAt = db.Column(db.DateTime, name='ExpiresAt')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow, name='CreatedAt')


class Purchases(db.Model):
    __tablename__ = 'Purchases'
    Id = db.Column(db.Integer, primary_key=True, name='Id')
    CustomerId = db.Column(db.Integer, db.ForeignKey('Customers.Id'), nullable=False, name='CustomerId')
    PurchaseDate = db.Column(db.DateTime, default=datetime.utcnow, name='PurchaseDate')
    ListingPrice = db.Column(db.Float, name='ListingPrice')
    SalePrice = db.Column(db.Float, name='SalePrice')
    DiscountPercentage = db.Column(db.Float, name='DiscountPercentage')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow, name='CreatedAt')


if __name__ == "__main__":
    app.run(debug=True)
