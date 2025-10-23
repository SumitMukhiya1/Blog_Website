from flask import Flask
from flask_login import LoginManager

#Importing Routes
from all_routes.models import User, db
from all_routes.main_routes import init_main_routes
from all_routes.authentication_routes import init_auth_routes
from all_routes.post_routes import init_post_routes
from all_routes.comment_routes import init_comment_routes
from all_routes.other_routes import init_other_routes
from all_routes.config import init_config

#SetUp App
app = Flask(__name__)
init_config(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"  # redirect if not logged in

#Give SqlAlchemy our app now it works with requests
db.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#all routes
init_main_routes(app)
init_auth_routes(app)
init_post_routes(app)
init_comment_routes(app)
init_other_routes(app)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)