from flask_login import LoginManager


def init_config(app):
    app.secret_key = "ghggfy7eyughgcyhe"

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False