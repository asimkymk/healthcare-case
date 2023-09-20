from datetime import datetime
from . import db

class Purchases(db.Model):
    __tablename__ = 'Purchases'
    Id = db.Column(db.Integer, primary_key=True)
    CustomerId = db.Column(db.Integer, db.ForeignKey('Customers.Id'), nullable=False)
    PurchaseDate = db.Column(db.DateTime, default=datetime.utcnow)
    ListingPrice = db.Column(db.Float)
    SalePrice = db.Column(db.Float)
    DiscountPercentage = db.Column(db.Float)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
