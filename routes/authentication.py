from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user
from routes.models_routes import User, db
from datetime import date
from flask_bcrypt import Bcrypt, check_password_hash

bcrypt = Bcrypt()


def authentication_route(app):
    @app.route('/signup', methods=['GET', 'POST'])
    def signup_page():
        if current_user.is_authenticated:
            return redirect(url_for('home_page'))
        if request.method == 'POST':
            print("✅ SIGNUP POST REQUEST RECEIVED")  # Debug
            print(f"Form data: {request.form}")
            fullname = request.form['fullname']
            email = request.form['email']
            password = request.form['password']
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(
                fullname=fullname,
                email=email,
                password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()

            print("user added sucessfully")

            return redirect(url_for('login_page'))
        return render_template('signup.html')


    @app.route('/login',methods=['GET', 'POST'])
    def login_page():
        if current_user.is_authenticated:
            return redirect(url_for('home_page'))
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("No account found with that email")
                return render_template('login.html')
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('home_page'))
            else:
                flash("Incorrect password")
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register_page():
        if current_user.is_authenticated:
            return redirect(url_for('home_page'))
        return render_template('register.html')