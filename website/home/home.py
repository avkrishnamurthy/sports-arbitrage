from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

home_ = Blueprint('home', __name__, template_folder='templates', static_url_path='home/', static_folder='static')


@home_.route('/home')
def home():
    """
    Page users are redirected to after sign up or log in
    Should explain the website and how it works and how it can be used
    """
    return render_template("home.html", user=current_user)