from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Customers(db.Model):
    __tablename__ = 'Customers'
    Id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    Surname = db.Column(db.String(50), nullable=False)
    Gsm = db.Column(db.String(20))
    Gender = db.Column(db.String(10))
    Birthday = db.Column(db.Date)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
