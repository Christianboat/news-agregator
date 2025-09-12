from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class NewsItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    summary = db.Column(db.Text)
    published = db.Column(db.DateTime, index=True)
    category = db.Column(db.String(100))
    image_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class SocialMediaScript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    news_item_id = db.Column(db.Integer, db.ForeignKey('news_item.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    news_item = db.relationship('NewsItem', backref=db.backref('scripts', lazy=True))

@login.user_loader
def load_user(id):
    return User.query.get(int(id))