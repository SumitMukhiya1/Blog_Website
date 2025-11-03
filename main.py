import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, login_required, logout_user
from datetime import date
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ====================== CONFIGURATION ======================

# Secret key
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-key-for-development")

# Database URL (Render PostgreSQL fix)
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
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 1000 MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# ====================== EXTENSIONS ======================
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"

# Import models & routes AFTER app init
from routes.models_routes import User, Link, Skill, Post, Comment, db
from routes.authentication import authentication_route
from routes.profile_route import edit_profile

# Initialize database
db.init_app(app)

# Create tables ONCE when app starts
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")

# ====================== LOGIN MANAGER ======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints/routes
authentication_route(app)
edit_profile(app)

# ====================== ROUTES ======================

@app.route('/')
def home_page():
    if not current_user.is_authenticated:
        return redirect(url_for('landing_page'))

    user_info = {
        "fullname": current_user.fullname,
        "email": current_user.email,
        "profile_image": current_user.profile_image,
        "user_name": current_user.user_name,
    }

    blogs = Post.query.order_by(Post.date.desc()).all()
    posts = []

    for blog in blogs:
        user = User.query.filter_by(id=blog.user_id).first()
        user_name = user.fullname if user else "Unknown User"
        user_profile_image = user.profile_image if user else None

        comments_section = Comment.query.filter_by(blog_id=blog.id).all()
        comments_list = []
        for c in comments_section:
            comment_user = User.query.get(c.user_id)
            comments_list.append({
                "content": c.content,
                "date": c.date.strftime('%b %d, %Y'),
                "user_name": comment_user.fullname if comment_user else "Unknown User",
                "user_profile_image": comment_user.profile_image if comment_user else None
            })

        blog_image = None
        if blog.image:
            image_path = os.path.join(app.config['FEATURED_IMAGE_FOLDER'], blog.image)
            if os.path.exists(image_path):
                blog_image = blog.image

        posts.append({
            "title": blog.title,
            "content": blog.content,
            "image": blog_image,
            "name": user_name,
            "profile_image": user_profile_image,
            "date": blog.date,
            "id": blog.id,
            "Comments": comments_list
        })

    # Add joined date for first-time users
    if not current_user.joined:
        current_user.joined = str(date.today())
        db.session.commit()

    return render_template('home.html', user_info=user_info, blogs=posts)

# ---------------------- PROFILE PAGE ----------------------
@app.route('/profile')
@login_required
def user_profile():
    user_links = Link.query.filter_by(user_id=current_user.id).all()
    user_skills = Skill.query.filter_by(user_id=current_user.id).all()
    user_all_blogs = Post.query.filter_by(user_id=current_user.id).all()

    user_info = {
        "fullname": current_user.fullname,
        "email": current_user.email,
        "profile_image": current_user.profile_image,
        "user_name": current_user.user_name,
        "about": current_user.about,
        "profession": current_user.profession,
        "bio": current_user.bio,
        "education": current_user.education,
        "location": f"{current_user.country} || {current_user.city}",
        "joined": current_user.joined,
        "links": user_links,
        "skills": [skill.skill for skill in user_skills],
        "user_all_blogs": str(len(user_all_blogs)),
        "user_posts": user_all_blogs
    }

    return render_template('profile.html', user_info=user_info)

# ---------------------- LANDING PAGE ----------------------
@app.route('/landing_page')
def landing_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    return render_template('landing_page.html')

# ---------------------- CREATE POST ----------------------
@app.route('/make_post', methods=['GET', 'POST'])
@login_required
def make_post():
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    if request.method == 'POST':
        post_featured_image = request.files.get('featured_image')
        image_filename = None

        if post_featured_image and post_featured_image.filename != '':
            if allowed_file(post_featured_image.filename):
                filename = secure_filename(post_featured_image.filename)
                image_path = os.path.join(app.config['FEATURED_IMAGE_FOLDER'], filename)
                try:
                    post_featured_image.save(image_path)
                    image_filename = filename
                except Exception:
                    flash('Error saving image. Please try again.', 'danger')
            else:
                flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF.', 'danger')

        post_title = request.form.get('title')
        post_content = request.form.get('content')
        user_id = current_user.id

        if post_title and post_content:
            try:
                new_post = Post(title=post_title, content=post_content, user_id=user_id, image=image_filename)
                db.session.add(new_post)
                db.session.commit()
                flash('Post created successfully!', 'success')
                return redirect(url_for('make_post'))
            except Exception:
                db.session.rollback()
                flash('Error creating post. Please try again.', 'danger')
        else:
            flash('Please fill title and content fields.', 'danger')

    return render_template('make_post.html')

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

# ====================== RUN APP ======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
