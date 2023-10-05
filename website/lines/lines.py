from datetime import datetime
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from website import db
import requests
import json
import os
from dotenv import load_dotenv
from website.models import Games
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from sqlalchemy import or_




lines_ = Blueprint('lines', __name__, template_folder='templates', static_url_path='lines/', static_folder='static')

load_dotenv()

API_KEY = os.getenv("API_KEY")
MARKETS = "h2h"
TOGGLE_LIVE = True
REGIONS = "us"
ODDS_FORMAT = "american"
BOOKMAKERS = "fanduel,draftkings,betmgm,foxbet,barstool,pointsbetus,circasports,wynnbet,unibet_us,betus,twinspires,betonlineag"
SPORTS = [
    "basketball_nba",
    "americanfootball_nfl",
    "icehockey_nhl",
    "americanfootball_ncaaf",
    "baseball_mlb",
]

# VARIABLES
SPORT = "americanfootball_nfl"
DAYS_FROM = "3"

# API CALL
def get_api_data():
    data_list = []
    for sport in SPORTS:
        request_url = "https://api.the-odds-api.com/v4/sports/{sport}/scores/?apiKey={api_key}&daysFrom={days_from}".format(
        sport = sport,
        api_key= API_KEY,
        days_from = DAYS_FROM
        )
        response = requests.get(request_url)
        data = response.json()
        data_list.append(data)
    return data_list


# HELPER FUNCTION TO PARSE API JSON RESPONSE
def extract_scores(item):
    home_score = None
    away_score = None
    if item['scores']:
        for score in item['scores']:
            if score['name'] == item['home_team']:
                home_score = int(score['score'])
            elif score['name'] == item['away_team']:
                away_score = int(score['score'])
    return home_score, away_score


def insert_scores():
    data_list = get_api_data()
    if not data_list:
        return
    for data in data_list:
        if not data: continue
        for item in data:
            home_score, away_score = extract_scores(item)
            item['home_team_score'] = home_score
            item['away_team_score'] = away_score
            stmt = insert(Games).values(
            id=item['id'],
            sport_key=item['sport_key'],
            sport_title=item['sport_title'],
            commence_time=item['commence_time'],
            completed=item['completed'],
            home_team=item['home_team'],
            away_team=item['away_team'],
            home_team_score=item['home_team_score'],
            away_team_score=item['away_team_score'],
            last_update=item['last_update']
        )
        
            update_dict = {
                Games.sport_key: item['sport_key'],
                Games.sport_title: item['sport_title'],
                Games.commence_time: item['commence_time'],
                Games.completed: item['completed'],
                Games.home_team: item['home_team'],
                Games.away_team: item['away_team'],
                Games.home_team_score: item['home_team_score'],
                Games.away_team_score: item['away_team_score'],
                Games.last_update: item['last_update']
            }

            stmt = stmt.on_conflict_do_update(
                index_elements=[Games.id],
                set_=update_dict,
                where=(Games.last_update.is_(None)
            ))

            db.session.execute(stmt)
    db.session.commit()

@lines_.route('/lines')
@login_required
def lines():
    return render_template("lines.html", user=current_user)


@lines_.route('/lines/sports')
@login_required
def sports():
    request_url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    data = requests.get(request_url)
    data = data.json()
    return data

@lines_.route('/lines/scores')
@login_required
def scores():
    current_date = datetime.now().date()
    games_today = db.session.query(Games).filter(func.date(Games.commence_time) > current_date).all()
    if len(games_today) == 0: 
        insert_scores()
    return games_today[0].home_team


@lines_.route('/insert_scores', methods=['POST'])
def call_insert_scores():
    insert_scores()  # Assuming insert_scores is defined elsewhere in your app
    return redirect(url_for('lines.search_games'))  # Redirect back to the search games page after inserting scores

@lines_.route('/search_games', methods=['GET', 'POST'])
def search_games():
    games = []
    if request.method == 'POST':
        query = db.session.query(Games)
        
        # Filtering based on user input
        date_query = request.form.get('date')
        if date_query:
            date_object = datetime.strptime(date_query, '%Y-%m-%d').date()
            query = query.filter(func.DATE(Games.commence_time) == date_object)
            
        team_query = request.form.get('team')
        if team_query:
            query = query.filter((Games.home_team == team_query) | (Games.away_team == team_query))
            
        sport_title_query = request.form.get('sport_title')
        if sport_title_query:
            query = query.filter(Games.sport_title == sport_title_query)
            
        games = query.all()
    
    return render_template('games.html', games=games, user=current_user)



@lines_.route('/lines/odds')
@login_required
def upcoming_odds():

    request_url = "https://api.the-odds-api.com/v4/sports/{sport}/odds/?regions={regions}&oddsFormat={odds_format}&markets={markets}&apiKey={api_key}&commenceTimeFrom=".format(
        sport="upcoming",
        api_key=API_KEY,
        markets=MARKETS,
        regions=REGIONS,
        odds_format=ODDS_FORMAT,
    )
    data = requests.get(request_url)
    return data.json()

