from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from website.models import Person
from werkzeug.security import generate_password_hash, check_password_hash
from website import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__, template_folder='templates')

@auth.route('/')
def default():
    return render_template("default.html")

@auth.route('/login', methods=['GET', 'POST'])
def login():
    #Don't want already logged in users to log in again
    if current_user.is_authenticated:
        return redirect(url_for('home.home', _external=True))
    #If trying to log in, get username and password
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        #Check if hashed password matches hash/salted password in DB
        user = Person.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('home.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Username does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    #Don't let logged in users sign up again
    if current_user.is_authenticated:
        return redirect(url_for('users.profile', username=current_user.username, _external=True))
    if request.method == 'POST':
        #POST request means they have submitted sign up
        email = request.form.get('email')
        username = request.form.get('username')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        email_user = Person.query.filter_by(email=email).first()
        username_user = Person.query.filter_by(username=username).first()
        #Sign up constraints, don't want too easy password
        if email_user:
            flash('Email already in use.', category='error')
        elif username_user:
            flash("Username already in use.", category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        elif len(username) > 17:
            flash('Username must be less than 18 characters')
        else:
            new_user = Person(email=email, username=username, first_name=first_name, password=generate_password_hash(
                password1, method='scrypt'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('home.home'))

    return render_template("create_account.html", user=current_user)