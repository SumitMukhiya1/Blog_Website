import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, login_required, logout_user
from datetime import date
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()
# Importing routes
from routes.models_routes import User, db, Link, Skill, Post, Comment
from routes.authentication import authentication_route
from routes.profile_route import edit_profile

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
app.config['FEATURED_IMAGE_FOLDER'] = 'static/featured_images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FEATURED_IMAGE_FOLDER'], exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 1000 MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FEATURED_IMAGE_FOLDER'], exist_ok=True)

login_manager = LoginManager(app)
login_manager.login_view = "login_page"

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Database of user
db.init_app(app)
bcrypt = Bcrypt(app)

# Authentication route
authentication_route(app)

# Edit profile route
edit_profile(app)


@app.route('/')
def home_page():
    if current_user.is_authenticated:
        user_info = {
            "fullname": current_user.fullname,
            "email": current_user.email,
            "profile_image": current_user.profile_image,
            "user_name": current_user.user_name,
        }
        blogs = Post.query.all()
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

            # FIXED: Check if image exists and handle missing images
            blog_image = None
            if blog.image:
                image_path = os.path.join(app.config['FEATURED_IMAGE_FOLDER'], blog.image)
                if os.path.exists(image_path):
                    blog_image = blog.image
                else:
                    print(f"DEBUG: Image not found: {image_path}")
                    blog_image = None

            posts.append({
                "title": blog.title,
                "content": blog.content,
                "image": blog_image,  # This will be None if image doesn't exist
                "name": user_name,
                "profile_image": user_profile_image,
                "date": blog.date,
                "id": blog.id,
                "Comments": comments_list
            })

        if not current_user.joined:
            current_user.joined = str(date.today())
            db.session.commit()
    else:
        return redirect(url_for('landing_page'))

    return render_template('home.html', user_info=user_info, blogs=posts)



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


@app.route('/landing_page')
def landing_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    return render_template('landing_page.html')


@login_required
@app.route('/make_post', methods=['GET', 'POST'])
def make_post():
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    if request.method == 'POST':
        # Getting featured image
        post_featured_image = request.files.get('featured_image')
        image_filename = None

        if post_featured_image and post_featured_image.filename != '':
            if allowed_file(post_featured_image.filename):
                filename = secure_filename(post_featured_image.filename)
                image_path = os.path.join(app.config['FEATURED_IMAGE_FOLDER'], filename)

                try:
                    post_featured_image.save(image_path)
                    image_filename = filename
                except Exception as e:
                    flash('Error saving image. Please try again.', 'danger')
            else:
                flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF.', 'danger')

        # Getting other info
        post_title = request.form.get('title')
        post_content = request.form.get('content')
        user_id = current_user.id

        # Save post in database
        if post_title and post_content:
            try:
                new_post = Post(
                    title=post_title,
                    content=post_content,
                    user_id=user_id,
                    image=image_filename,
                )
                db.session.add(new_post)
                db.session.commit()
                flash('Post created successfully!', 'success')
                return redirect(url_for('make_post'))
            except Exception as e:
                db.session.rollback()
                flash('Error creating post. Please try again.', 'danger')
        else:
            flash('Please fill title and content fields.', 'danger')

    return render_template('make_post.html')


@app.route('/remove-skill', methods=['POST'])
def remove_skill():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Not logged in'})

    data = request.get_json()
    skill_to_remove = data.get('skill')

    if not skill_to_remove:
        return jsonify({'success': False, 'message': 'No skill provided'})

    try:
        skill_record = Skill.query.filter_by(
            user_id=current_user.id,
            skill=skill_to_remove
        ).first()

        if skill_record:
            db.session.delete(skill_record)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Skill removed successfully'})
        else:
            return jsonify({'success': False, 'message': 'Skill not found'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/delete-link/<int:link_id>', methods=['POST'])
def delete_link(link_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Not logged in'})

    link = Link.query.get(link_id)
    if link and link.user_id == current_user.id:
        db.session.delete(link)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Link deleted successfully'})
    else:
        return jsonify({'success': False, 'message': 'Link not found or access denied'})


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
    blog_id = int(blog_id_str)

    if not current_user.is_authenticated:
        flash("You must be logged in to comment.", "warning")
        return redirect(url_for('login_page'))
    user_id = int(current_user.id)

    new_comment = Comment(user_id=user_id, blog_id=blog_id, content=content)
    db.session.add(new_comment)
    db.session.commit()

    flash("Comment added successfully!", "success")
    return redirect(url_for('home_page'))

@app.route('/sign_out')
def sign_out():
    logout_user()
    return render_template('landing_page.html')


if __name__ == '__main__':
    app.run()