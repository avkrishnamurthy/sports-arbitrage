from datetime import datetime
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from website import db
import requests
import json
import os
from dotenv import load_dotenv
from website.models import Games, Bookmakers, Odds
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound

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
    "americanfootball_ncaaf",
    "baseball_mlb",
]
DAYS_FROM = "3"



# API CALL
def get_games_api_data():
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
    data_list = get_games_api_data()
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

@lines_.route('/insert_scores', methods=['POST'])
def call_insert_scores():
    insert_scores() 
    return redirect(url_for('lines.search_games'))

@lines_.route('/lines/games', methods=['GET', 'POST'])
def search_games():
    games = []
    if request.method == 'POST':
        query = db.session.query(Games)
        
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

#TODO: make it match current date – needs to be in sync with games fetch
ODDS_COMMENCE_TIME_FROM = "2023-10-01T00:00:00Z"
def get_odds_api_data():
    data_list = []
    for sport in SPORTS:
        request_url = "https://api.the-odds-api.com/v4/sports/{sport}/odds?apiKey={api_key}&regions={regions}&markets={markets}&dateFormat=iso&oddsFormat={odds_format}&commenceTimeFrom={commence_time_from}".format(
        sport=sport,
        api_key=API_KEY,
        markets=MARKETS,
        regions=REGIONS,
        odds_format=ODDS_FORMAT,
        commence_time_from=ODDS_COMMENCE_TIME_FROM
        )
        response = requests.get(request_url)
        data = response.json()
        data_list.append(data)
    return data_list

def insert_odds():
    data_list = get_odds_api_data() 
    if not data_list:
        return
    for data in data_list:
        if not data:
            continue
        for item in data:
            if not item: continue
            # Check if the game_id exists in the Games table
            print(item)
            game_id = item['id']
            try:
                game = db.session.query(Games).filter_by(id=game_id).one()
            except NoResultFound:
                continue  # Skip inserting odds if game_id doesn't exist in Games

            for bookmaker in item['bookmakers']:
                # Get or create the bookmaker
                bookmaker_obj, _ = get_or_create(db.session, Bookmakers, key=bookmaker['key'], defaults={'title': bookmaker['title']})
                
                for market in bookmaker['markets']:
                    home_team_odds = None
                    away_team_odds = None
                    draw_odds = None
                    if market['key'] == "h2h":
                        for outcome in market['outcomes']:
                            outcome_name = outcome['name']
                            if outcome_name == item['home_team']:
                                home_team_odds = outcome['price']
                            elif outcome_name == item['away_team']:
                                away_team_odds = outcome['price']
                            elif outcome_name == 'Draw':
                                draw_odds = outcome['price']
                            
                        stmt = insert(Odds).values(
                            game_id=game.id,
                            bookmaker_id=bookmaker_obj.id,
                            home_team_odds = home_team_odds,
                            away_team_odds = away_team_odds,
                            sport_key=item['sport_key'],
                            sport_title=item['sport_title'],
                            draw_odds = draw_odds,
                            last_update=market['last_update']
                        )

                        update_dict = {
                            Odds.home_team_odds: home_team_odds,
                            Odds.away_team_odds: away_team_odds,
                            Odds.draw_odds: draw_odds,
                            Odds.last_update: market['last_update']
                        }

                        stmt = stmt.on_conflict_do_update(
                            index_elements=[Odds.game_id, Odds.bookmaker_id],
                            set_=update_dict,
                            where=(Odds.last_update.is_(None) | (Odds.last_update < market['last_update']))
                        )

                        db.session.execute(stmt)

    db.session.commit()

@lines_.route('/insert_odds', methods=['POST'])
def call_insert_odds():
    insert_odds() 
    return redirect(url_for('lines.search_odds'))


@lines_.route('/lines/odds', methods=['GET', 'POST'])
def odds():
    odds = []
    if request.method == 'POST':
        query = db.session.query(Odds).join(Games).join(Bookmakers)
        date_query = request.form.get('date')
        if date_query:
            date_object = datetime.strptime(date_query, '%Y-%m-%d').date()
            query = query.filter(func.DATE(Games.commence_time) == date_object)
            
        team_query = request.form.get('team')
        if team_query:
            query = query.filter((Games.home_team == team_query) | (Games.away_team == team_query))
            
        bookmaker_query = request.form.get('bookmaker')
        if bookmaker_query:
            query = query.filter(Bookmakers.title == bookmaker_query)
        
        odds = query.all()

    return render_template('odds.html', odds=odds, user=current_user)


def get_or_create(session, model, defaults=None, **kwargs):
    """
    Gets an object or creates and returns the object if not exists
    """
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        return instance, False
    else:
        params = {**kwargs, **(defaults or {})}
        instance = model(**params)
        session.add(instance)
        session.commit()
        return instance, True