from flask import render_template
from all_routes.models import BlogPost, Comment


def init_main_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    def home_page():
        all_posts = BlogPost.query.all()
        posts_list = []
        for post in all_posts:
            comments = Comment.query.filter_by(post_id=post.id).all()
            posts_list.append({
                "post_id": post.id,
                "author": post.author,
                "author_image": post.author_image,
                "title": post.title,
                "image": post.image,
                "description": post.description,
                "date": post.date,
                "comments": comments
            })

        return render_template('home.html', posts=posts_list)