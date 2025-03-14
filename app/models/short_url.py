import random
import string
from datetime import datetime
from app import db

def generate_short_code(length=6):
    """Generate a random short code of specified length using A-Z and 0-9"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

class ShortURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    target_url = db.Column(db.String(2048), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    visits = db.relationship('Visit', backref='short_url', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ShortURL {self.short_code}>'
    
    @classmethod
    def create_with_unique_code(cls, target_url, user_id, custom_code=None):
        """Create a new short URL with either a custom code or a unique generated one"""
        if custom_code:
            # Check if custom code already exists
            existing = cls.query.filter_by(short_code=custom_code).first()
            if existing:
                return None, "This short code is already in use"
            
            short_code = custom_code
        else:
            # Generate a unique short code
            while True:
                short_code = generate_short_code()
                if not cls.query.filter_by(short_code=short_code).first():
                    break
        
        # Create new short URL
        short_url = cls(short_code=short_code, target_url=target_url, user_id=user_id)
        db.session.add(short_url)
        db.session.commit()
        
        return short_url, None