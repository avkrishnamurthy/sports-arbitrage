from datetime import datetime
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
import pytz
from website import db
import requests
import json
import os
from dotenv import load_dotenv
from website.models import Bookmakers, Odds, Person, Games
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import contains_eager

users_ = Blueprint('users', __name__, template_folder='templates', static_url_path='users/static', static_folder='static')

load_dotenv()

@users_.route('/check-user-exists', methods=['POST'])
@login_required
def check_user_exists():
    """
    Endpoint used to validate if a user exists
    Used for user search feature 
    """
    username = request.json.get('username')
    #Safe against sql injection because sqlalchemy automatically escapes parameters
    user = Person.query.filter_by(username=username).first()
    user_exists = True if user else False
    return jsonify({'exists': user_exists})


@users_.route('/users/<username>', methods=['GET'])
@login_required
def profile(username):
    """
    Endpoint for profile
    Will either be for the current user's profile, or the profile of a user they are visiting
    If current user's profile, they get more data and have options to modify data
    If other user's profile, they have less data and no write authorization
    """
    user = Person.query.filter_by(username=username).first()
    favorite_bookmaker = Bookmakers.query.filter_by(id=user.favorite_bookmaker_id).first()
    if not user: 
        flash("User does not exist", category="error")
        return redirect(url_for("home.home", _external=True))
    
    following_users = set(user.following.all())
    follower_users = set(user.follower.all())
    games_odds_modified = []
    if user.favorite_team:
        #Safe against sql injection
        #Utilizes SQLAlchemy parameterized queries that automatically escapes parameters passed in
        #Instead of doing '%' + user.favorite_team + '%', which would be at risk
        user_favorite_team_pattern = '%{}%'.format(user.favorite_team)
        #Filtered to show upcoming games (almost acts like a schedule and potential win probability for the user's favorite team)
        now = datetime.now()
        games_odds = db.session.query(Games) \
            .outerjoin(Odds, Games.id == Odds.game_id) \
            .add_columns(
                Games.id,
                Games.sport_key,
                Games.sport_title,
                Games.commence_time,
                Games.completed,
                Games.home_team,
                Games.away_team,
                Games.home_team_score,
                Games.away_team_score,
                Games.last_update,
                Odds.home_team_odds,
                Odds.away_team_odds ) \
            .filter((Games.home_team.ilike(user_favorite_team_pattern)) | (Games.away_team.ilike(user_favorite_team_pattern))) \
            .filter((Games.commence_time > now)) \
            .filter((Odds.bookmaker_id == user.favorite_bookmaker_id) | (Odds.bookmaker_id.is_(None))) \
            .all()
        

        #Cleaning up odds and time display on frontend
        for game_odd in games_odds:
            eastern = pytz.timezone('US/Eastern')
            commence_time_eastern = game_odd.commence_time
            if commence_time_eastern:
                commence_time_eastern = commence_time_eastern.astimezone(eastern)
                commence_time_eastern = commence_time_eastern.strftime('%b %d, %-I:%M %p ET')
            home_team_odds = ""
            if game_odd.home_team_odds:
                home_team_odds = game_odd.home_team_odds
                if game_odd.home_team_odds > 0: home_team_odds = f"+{game_odd.home_team_odds}"
            away_team_odds = ""
            if game_odd.away_team_odds:
                away_team_odds = game_odd.away_team_odds
                if game_odd.away_team_odds > 0: away_team_odds = f"+{game_odd.away_team_odds}"
            game_odd_dict = {
                'id': game_odd.id,
                'sport_key': game_odd.sport_key,
                'sport_title': game_odd.sport_title,
                'commence_time': commence_time_eastern,
                'completed': game_odd.completed,
                'home_team': game_odd.home_team,
                'away_team': game_odd.away_team,
                'home_team_score': game_odd.home_team_score,
                'away_team_score': game_odd.away_team_score,
                'last_update': game_odd.last_update,
                'home_team_odds': home_team_odds,
                'away_team_odds': away_team_odds
            }

            games_odds_modified.append(game_odd_dict)
    if current_user.username == username: 
        bookmakers = Bookmakers.query.all()
        return render_template('my_profile.html', current_user = current_user, user=user, favorite_bookmaker=favorite_bookmaker, bookmakers=bookmakers, games=games_odds_modified, len=len, following=following_users, followers=follower_users)
    return render_template('profile.html', current_user = current_user, user=user, favorite_bookmaker=favorite_bookmaker, games=games_odds_modified, len=len, following=following_users, followers=follower_users)


@users_.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    """
    Endpoint to follow a user
    Simply adds current user to list of user they requested to follow list of followers
    If they were already following, unfollows them
    """
    follow_json = json.loads(request.data)
    follow_username = follow_json['username']
    user = Person.query.filter_by(username=follow_username).first()
    if not user:
        flash("User does not exist", category="error")
        return redirect(url_for("users.profile", username=current_user.username))

    #Determines whether to follow or unfollow based on if user is currently following
    if current_user in user.follower:
        user.follower.remove(current_user)
    else:
        user.follower.append(current_user)
    
    db.session.commit()
    return redirect(url_for("users.profile", username=username))

@users_.route('users/<username>/team', methods=['POST'])
@login_required
def favorite_team(username):
    """
    Endpoint that allows users to set their favorite team (just to some string, since our database has no concept of a team table)
    """
    user = Person.query.filter_by(username=username).first()
    team_info = request.form.get('team')
    user.favorite_team = team_info
    db.session.commit()
    return redirect(url_for('users.profile', username=username))

@users_.route('users/<username>/bookmaker', methods=['POST'])
@login_required
def favorite_bookmaker(username):
    """
    Endpoint to allow users to set their favorite bookmaker
    Only allow users to select of bookmakers that are in the database on frontend
    """
    user = Person.query.filter_by(username=username).first()
    favorite_json = json.loads(request.data)
    favorite_id = favorite_json['favoriteId']
    user.favorite_bookmaker_id = favorite_id
    db.session.commit()
    return jsonify({})
