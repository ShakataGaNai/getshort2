from datetime import datetime
from app import db

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_url_id = db.Column(db.Integer, db.ForeignKey('short_url.id'), nullable=False)
    ip_address = db.Column(db.String(45)) # Supporting IPv6
    user_agent = db.Column(db.String(255))
    browser = db.Column(db.String(50))
    browser_version = db.Column(db.String(20))
    device_type = db.Column(db.String(20)) # mobile, tablet, desktop
    operating_system = db.Column(db.String(50))
    country_code = db.Column(db.String(2))
    country_name = db.Column(db.String(50))
    city = db.Column(db.String(50))
    referrer = db.Column(db.String(2048))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Visit {self.id} for ShortURL {self.short_url_id}>'