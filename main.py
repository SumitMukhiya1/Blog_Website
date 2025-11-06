import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, login_required, logout_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from routes.models_routes import User, Link, Skill, Post, Comment, db

# Load environment variables
load_dotenv()
app = Flask(__name__)
# ====================== CONFIGURATION ======================
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-key-for-development")

db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or "sqlite:///local_database.db"

# Upload folders
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
app.config['FEATURED_IMAGE_FOLDER'] = 'static/featured_images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FEATURED_IMAGE_FOLDER'], exist_ok=True)

# File upload rules
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 1000 MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# ====================== EXTENSIONS ======================
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"

# Initialize database
db.init_app(app)
# ====================== LOGIN MANAGER ======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes
from routes.authentication import authentication_route
from routes.profile_route import edit_profile
from routes.home_routes import home_route
from routes.make_post_routes import make_post_routes


authentication_route(app)
edit_profile(app)
home_route(app)
make_post_routes(app)

# ---------------------- LANDING PAGE ----------------------
@app.route('/landing_page')
def landing_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    return render_template('landing_page.html')

# ---------------------- REMOVE SKILL ----------------------
@app.route('/remove-skill', methods=['POST'])
def remove_skill():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Not logged in'})

    data = request.get_json()
    skill_to_remove = data.get('skill')

    if not skill_to_remove:
        return jsonify({'success': False, 'message': 'No skill provided'})

    try:
        skill_record = Skill.query.filter_by(user_id=current_user.id, skill=skill_to_remove).first()
        if skill_record:
            db.session.delete(skill_record)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Skill removed successfully'})
        return jsonify({'success': False, 'message': 'Skill not found'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# ---------------------- DELETE LINK ----------------------
@app.route('/delete-link/<int:link_id>', methods=['POST'])
def delete_link(link_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Not logged in'})

    link = Link.query.get(link_id)
    if link and link.user_id == current_user.id:
        db.session.delete(link)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Link deleted successfully'})
    return jsonify({'success': False, 'message': 'Link not found or access denied'})

# ---------------------- COMMENT ----------------------
@app.route('/comment', methods=['POST'])
def comment():
    content = request.form.get("content", "").strip()
    if not content:
        flash("Comment cannot be empty.", "warning")
        return redirect(url_for('home_page'))

    blog_id_str = request.form.get("blog_id")
    if not blog_id_str or not blog_id_str.isdigit():
        flash("Invalid blog ID.", "danger")
        return redirect(url_for('home_page'))

    if not current_user.is_authenticated:
        flash("You must be logged in to comment.", "warning")
        return redirect(url_for('login_page'))

    new_comment = Comment(user_id=current_user.id, blog_id=int(blog_id_str), content=content)
    db.session.add(new_comment)
    db.session.commit()

    flash("Comment added successfully!", "success")
    return redirect(url_for('home_page'))

# ---------------------- SIGN OUT ----------------------
@app.route('/sign_out')
def sign_out():
    logout_user()
    return render_template('landing_page.html')

@app.route('/post_detail/<int:post_id>', methods=['GET', "POST"])
def post_detail(post_id):
    blog = Post.query.get(post_id)
    user = User.query.get(blog.user_id)
    comments = Comment.query.filter_by(blog_id=post_id).all()
    # Prepare comments data with user info
    comments_data = []

    for comment in comments:
        comment_user = User.query.get(comment.user_id)
        comments_data.append({
            "content": comment.content,
            "date": comment.date.strftime("%B %d, %Y"),
            "fullname": User.query.get(comment.user_id).fullname,
            "profile_image": User.query.get(comment.user_id).profile_image,
        })

    # Prepare blog data
    blogs_data = {
        "title": blog.title,
        "profile_image": user.profile_image,  # blog author image
        "featured_image": blog.image,
        "fullname": user.fullname,
        "date": blog.date.strftime("%B %d, %Y"),
        "content": blog.content,
        "bio": user.bio,
        "comments": comments_data,
        "blog_id": post_id
    }

    return render_template('post_detail.html', blog_data=blogs_data)

@app.route('/post_detail_comment', methods=['GET','POST'])
def post_detail_comment():
    if request.method == "POST":
        blog_id = request.form.get("blog_id")
        if blog_id:
            user_id = current_user.id
            content = request.form.get('content')
            new_comment = Comment(user_id=int(user_id), blog_id=int(blog_id), content=content)
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('post_detail', post_id=blog_id))
    return render_template(url_for('home.html'))

# ====================== RUN APP ======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)