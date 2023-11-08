from datetime import datetime
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from website import db
import requests
import json
import os
from dotenv import load_dotenv
from website.models import Bookmakers, Person
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

users_ = Blueprint('users', __name__, template_folder='templates', static_url_path='users/static', static_folder='static')

load_dotenv()

@users_.route('/check-user-exists', methods=['POST'])
def check_user_exists():
    username = request.json.get('username')
    user = Person.query.filter_by(username=username).first()
    user_exists = True if user else False
    return jsonify({'exists': user_exists})


@users_.route('/users/<username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    user = Person.query.filter_by(username=username).first()
    favorite_bookmaker = Bookmakers.query.filter_by(id=user.favorite_bookmaker_id).first()
    if not user: 
        flash("User does not exist", category="error")
        return redirect(url_for("home.home", _external=True))

    if current_user.username == username: 
        bookmakers = Bookmakers.query.all()
        return render_template('my_profile.html', current_user = current_user, favorite_bookmaker=favorite_bookmaker, bookmakers=bookmakers)
    return render_template('profile.html', current_user = current_user, user=user, favorite_bookmaker=favorite_bookmaker)


@users_.route('users/<username>/team', methods=['POST'])
@login_required
def favorite_team(username):
    user = Person.query.filter_by(username=username).first()
    team_info = request.form.get('team')
    user.favorite_team = team_info
    db.session.commit()
    return redirect(url_for('users.profile', username=username))

@users_.route('users/<username>/bookmaker', methods=['POST'])
@login_required
def favorite_bookmaker(username):
    user = Person.query.filter_by(username=username).first()
    favorite_json = json.loads(request.data)
    favorite_id = favorite_json['favoriteId']
    user.favorite_bookmaker_id = favorite_id
    db.session.commit()
    return jsonify({})
