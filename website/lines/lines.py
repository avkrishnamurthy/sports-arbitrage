from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from website import db
import json

lines_ = Blueprint('lines', __name__, template_folder='templates', static_url_path='lines/', static_folder='static')


@lines_.route('/lines')
@login_required
def lines():
    return render_template("lines.html", user=current_user)