from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

home_ = Blueprint('home', __name__, template_folder='templates', static_url_path='home/', static_folder='static')


@home_.route('/home')
@login_required
def home():
    return render_template("home.html", user=current_user)