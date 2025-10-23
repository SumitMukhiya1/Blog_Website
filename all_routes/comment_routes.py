from flask import request, redirect, url_for
from flask_login import login_required, current_user
from all_routes.models import db, User, Comment

def init_comment_routes(app):
    @app.route('/comment/<int:post_id>', methods=['POST'])
    @login_required
    def post_comment(post_id):
        comment_text = request.form.get('comment')
        name = User.query.filter_by(id=current_user.id).first().username
        new_comment = Comment(content=comment_text, name=name, user_id=current_user.id, post_id=post_id)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('home_page'))