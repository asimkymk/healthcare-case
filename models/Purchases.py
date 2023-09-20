from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Purchases(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    listing_price = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    discount_percentage = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
