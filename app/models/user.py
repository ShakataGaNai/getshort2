from datetime import datetime, UTC
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    github_id = db.Column(db.Integer, unique=True, nullable=False)
    avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    short_urls = db.relationship('ShortURL', backref='creator', lazy=True)
    domain_modifiers = db.relationship('DomainModifier', backref='creator', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))