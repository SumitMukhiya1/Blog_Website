import os
from flask import render_template, redirect, url_for
from flask_login import current_user
from datetime import date
from routes.models_routes import User, Post, Comment, db

def home_route(app):
    @app.route('/', methods=['GET', 'POST'])
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