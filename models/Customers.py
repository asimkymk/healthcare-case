from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Customers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    gsm = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    birthday = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
