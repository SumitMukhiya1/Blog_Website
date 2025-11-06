import os
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from routes.models_routes import Post, db

def make_post_routes(app):
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
            category = request.form.get("category")
            tags = request.form.getlist("tags")
            excerpt = request.form.get("excerpt")

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