from flask import request, flash, redirect, url_for, render_template
from all_routes.models import User, db
from flask_login import login_user, logout_user

def init_auth_routes(app):

    @app.route('/login', methods=['GET', 'POST'])
    def login_page():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            user = User.query.filter_by(email=email).first()

            # Check if user exists AND password is correct
            if user and password == user.password_hash:
                login_user(user)  # This creates the login session
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard_page'))
            else:
                flash('Invalid email or password!', 'error')

        return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup_page():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            conform_password = request.form['conform_password']

            # Check if passwords match
            if password != conform_password:
                flash('Passwords do not match!', 'error')
                return redirect(url_for('signup_page'))

            # Check if user exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists!', 'error')
                return redirect(url_for('signup_page'))

            if User.query.filter_by(email=email).first():
                flash('Email already exists!', 'error')
                return redirect(url_for('signup_page'))

            # Create new user (plain password)
            new_user = User(username=username, email=email, password_hash=password)
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login_page'))

        return render_template('signup.html')

    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out successfully!', 'info')
        return redirect(url_for('home_page'))