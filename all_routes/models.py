from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Creating DataBase
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)  # Author name
    author_image = db.Column(db.String(), nullable=True)  # Author profile image
    title = db.Column(db.String(100), nullable=False)  # Post title
    image = db.Column(db.String(), nullable=True)  # Post image
    description = db.Column(db.String(), nullable=False)  # Short description
    content = db.Column(db.Text, nullable=True)  # Full post content
    date = db.Column(db.DateTime)  # ✅ new column


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)

    # Foreign keys
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

