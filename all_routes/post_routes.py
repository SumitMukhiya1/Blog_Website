from flask import request, redirect, url_for, render_template
from flask_login import login_required
from all_routes.models import BlogPost, db
from datetime import datetime

def init_post_routes(app):
    @app.route('/make_post', methods=['GET', 'POST'])
    @login_required
    def make_post():
        if request.method == 'POST':
            author_name = request.form.get('authorName')
            author_image = request.form.get('authorImage')
            post_title = request.form.get('postTitle')
            post_image = request.form.get('postImage')
            post_description = request.form.get('postDescription')

            new_post = BlogPost(
                author=author_name,
                author_image=author_image,
                title=post_title,
                image=post_image,
                description=post_description,
                content=post_description,
                date=datetime.now().date(),
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('home_page'))
        return render_template('make_post.html')

    @app.route('/dashboard')
    @login_required
    def dashboard_page():
        return render_template('dashboard.html')