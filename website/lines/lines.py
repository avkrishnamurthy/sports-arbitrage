from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from website import db
import requests
import json
import os
from dotenv import load_dotenv
from website.models import Games, Bookmakers, Odds, ArbitrageOpportunity
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound
from . import arbitrage
from sqlalchemy.orm import aliased
from celery import shared_task
import pytz

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

@shared_task(ignore_result=False)
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
                where=(Games.last_update.is_(None) | ((item['last_update'] is not None) and (Games.last_update < item['last_update'])))
            )

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

@lines_.route('/lines/games', methods=['GET'])
def search_games():

    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = db.session.query(Games)

    date_query = request.args.get('date')
    team1_query = request.args.get('team1')
    team2_query = request.args.get('team2')
    sport_title_query = request.args.get('sport_title')
    live_query = request.args.get('live')

    if live_query:
        now = datetime.now()

        one_day_earlier = now - timedelta(days=1)
        query = query.filter(
            (Games.commence_time >= one_day_earlier) & 
            (Games.commence_time < now) & 
            (Games.completed == False)
        )
        
    if date_query:
        date_object = datetime.strptime(date_query, '%Y-%m-%d').date()
        query = query.filter(func.DATE(Games.commence_time) == date_object)

    if team1_query:
        query = query.filter((Games.home_team.ilike('%' + team1_query + '%')) | (Games.away_team.ilike('%' + team1_query + '%')))

    if team2_query:
        query = query.filter((Games.home_team.ilike('%' + team2_query + '%')) | (Games.away_team.ilike('%' + team2_query + '%')))

    if sport_title_query:
        query = query.filter(Games.sport_title.ilike('%' + sport_title_query + '%'))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    games = pagination.items
    for game in games:
        eastern = pytz.timezone('US/Eastern')
        game_time_eastern = game.commence_time.astimezone(eastern)
        game.commence_time_display = game_time_eastern.strftime('%b %d, %-I:%M %p ET')
        last_update_eastern = game.last_update
        if last_update_eastern: 
            last_update_eastern = last_update_eastern.astimezone(eastern)
            last_update_eastern = last_update_eastern.strftime('%b %d, %-I:%M:%S %p ET')
        game.last_update_display = last_update_eastern

    
    return render_template('games.html', pagination=pagination, games=games, current_user=current_user)

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
                            where=(Odds.last_update.is_(None) | ((market['last_update'] is not None) and (Odds.last_update < market['last_update'])))
                        )

                        db.session.execute(stmt)

    db.session.commit()

@lines_.route('/insert_odds', methods=['POST'])
def call_insert_odds():
    insert_odds() 
    return redirect(url_for('lines.odds'))


@lines_.route('/lines/odds', methods=['GET'])
def odds():

    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = db.session.query(Odds).join(Games).join(Bookmakers)

    date_query = request.args.get('date')
    team1_query = request.args.get('team1')
    team2_query = request.args.get('team2')
    bookmaker_query = request.args.get('bookmaker')

    live_query = request.args.get('live')

    if live_query:
        now = datetime.now()

        one_day_earlier = now - timedelta(days=1)
        query = query.filter(
            (Games.commence_time >= one_day_earlier) & 
            (Games.commence_time < now) & 
            (Games.completed == False)
        )

    if date_query:
        date_object = datetime.strptime(date_query, '%Y-%m-%d').date()
        query = query.filter(func.DATE(Games.commence_time) == date_object)

    if team1_query:
        query = query.filter((Games.home_team.ilike('%' + team1_query + '%')) | (Games.away_team.ilike('%' + team1_query + '%')))

    if team2_query:
        query = query.filter((Games.home_team.ilike('%' + team2_query + '%')) | (Games.away_team.ilike('%' + team2_query + '%')))

    if bookmaker_query:
        query = query.filter(Bookmakers.title.ilike(f'%{bookmaker_query}%'))

    query = query.order_by(Odds.last_update.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    odds = pagination.items
    for odd in odds:
        odd.home_team_odds_display = odd.home_team_odds
        odd.away_team_odds_display = odd.away_team_odds
        if odd.home_team_odds > 0:
            odd.home_team_odds_display = '+'+str(odd.home_team_odds)
        if odd.away_team_odds > 0:
            odd.away_team_odds_display = '+'+str(odd.away_team_odds)

        eastern = pytz.timezone('US/Eastern')
        last_update_eastern = odd.last_update
        if last_update_eastern: 
            last_update_eastern = last_update_eastern.astimezone(eastern)
            last_update_eastern = last_update_eastern.strftime('%b %d, %-I:%M:%S %p ET')
        odd.last_update_display = last_update_eastern

    return render_template('odds.html', pagination=pagination, odds=odds, current_user=current_user)

@lines_.route('/insert_arbitrage', methods=['POST'])
def call_insert_arbitrage():
    arbitrage.insert_arbitrage() 
    return redirect(url_for('lines.arbitrage_opportunities'))

@lines_.route('/lines/arbitrage', methods=['GET'])
def arbitrage_opportunities():
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    AwayOdds = aliased(Odds)

    query = db.session.query(
        ArbitrageOpportunity,
        Games,
        Odds,
        AwayOdds
    ).join(
        Games, ArbitrageOpportunity.game_id == Games.id
    ).join(
        Odds, ArbitrageOpportunity.home_team_odds_id == Odds.id
    ).join(
        AwayOdds, ArbitrageOpportunity.away_team_odds_id == AwayOdds.id
    )

    date_query = request.args.get('date')
    team1_query = request.args.get('team1')
    team2_query = request.args.get('team2')
    if date_query:
        date_object = datetime.strptime(date_query, '%Y-%m-%d').date()
        query = query.filter(func.DATE(Games.commence_time) == date_object)

    if team1_query:
        query = query.filter((Games.home_team.ilike('%' + team1_query + '%')) | (Games.away_team.ilike('%' + team1_query + '%')))

    if team2_query:
        query = query.filter((Games.home_team.ilike('%' + team2_query + '%')) | (Games.away_team.ilike('%' + team2_query + '%')))
    

    query = query.order_by(ArbitrageOpportunity.time_found.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    arbitrages = pagination.items

    for arbitrage in arbitrages:
        arbitrage[0].profit_percentage_display = str(abs(round(arbitrage[0].profit_percentage, 2)) * 100)+"%"
        arbitrage[2].home_team_odds_display = arbitrage[2].home_team_odds
        arbitrage[3].away_team_odds_display = arbitrage[3].away_team_odds
        if arbitrage[2].home_team_odds > 0:
            arbitrage[2].home_team_odds_display = "+"+str(arbitrage[2].home_team_odds)
        if arbitrage[3].away_team_odds > 0:
            arbitrage[3].away_team_odds_display = "+"+str(arbitrage[3].away_team_odds)
        
        eastern = pytz.timezone('US/Eastern')
        arbitrage_time_eastern = arbitrage[0].time_found.astimezone(eastern)
        arbitrage[0].time_found_display = arbitrage_time_eastern.strftime('%b %d, %-I:%M %p ET')

    return render_template('arbitrage.html', pagination=pagination, arbitrages=arbitrages, current_user=current_user)



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