from datetime import datetime
from . import db

class Tokens(db.Model):
    __tablename__ = 'Tokens'
    Id = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.Id'), nullable=False)
    Token = db.Column(db.String(255), nullable=False)
    ExpiresAt = db.Column(db.DateTime)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
