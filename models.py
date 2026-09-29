from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import os

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='user', lazy=True, cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')
    social_accounts = db.relationship('SocialAccount', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class SocialAccount(db.Model):
    """Connected social media accounts"""
    __tablename__ = 'social_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # twitter, linkedin, instagram
    account_id = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255))
    access_token = db.Column(db.Text)  # Encrypted in production
    refresh_token = db.Column(db.Text)  # Encrypted in production
    token_expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_synced = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<SocialAccount {self.platform}:{self.username}>'

class Post(db.Model):
    """Social media posts with performance data"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    platform_post_id = db.Column(db.String(255))  # Original post ID from platform
    content = db.Column(db.Text, nullable=False)
    posted_at = db.Column(db.DateTime, nullable=False)
    
    # Performance metrics
    likes = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    
    # Calculated score
    performance_score = db.Column(db.Float, default=0.0)
    
    # Sync status
    is_synced = db.Column(db.Boolean, default=False)
    synced_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_performance_score(self):
        """Calculate weighted performance score"""
        return (self.likes * 1.0 + self.shares * 2.0 + self.comments * 1.5 + self.clicks * 0.5) / max(1, self.impressions / 100)
    
    def __repr__(self):
        return f'<Post {self.id} on {self.platform}>'

class Conversation(db.Model):
    """User conversations with the AI agent"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    context = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Conversation {self.id}>'

class Insight(db.Model):
    """Learned patterns and insights"""
    __tablename__ = 'insights'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pattern = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    success_rate = db.Column(db.Float, default=0.0)
    evidence_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Insight {self.pattern}>'
