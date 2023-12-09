from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from website import db
from dotenv import load_dotenv
from website.models import Games, Bookmakers, Odds, ArbitrageOpportunity
from sqlalchemy import func
from sqlalchemy.orm import aliased
import pytz
from . import the_odds_api

#blueprint for lines
lines_ = Blueprint('lines', __name__, template_folder='templates', static_url_path='lines/', static_folder='static')

@lines_.route('/lines/games', methods=['GET'])
@login_required
def search_games():
    """
    READ/GET endpoint for the games feature
    Endpoint that allows users to query database for any games
    Filter options: date, team 1, team 2, sport, live
    Utilizes pagination to improve query efficiency and make results more digestible
    """

    #Standard page size
    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = db.session.query(Games)

    #Getting query parameters from get request
    date_query = request.args.get('date')
    team1_query = request.args.get('team1')
    team2_query = request.args.get('team2')
    sport_title_query = request.args.get('sport_title')
    live_query = request.args.get('live')

    #Live game implementation
    #Gets current time, and if current time is past commence time and completed not set, we know it is live 
    if live_query:
        now = datetime.now()

        #one day earlier needed to ensure that if a game has gone past midnight, it is still being checked
        one_day_earlier = now - timedelta(days=1)
        #Also check that start time is earlier than current, and also that completed flag has not been set to true
        query = query.filter(
            (Games.commence_time >= one_day_earlier) & 
            (Games.commence_time < now) & 
            (Games.completed == False)
        )
        
    #Filtering games based on query parameters
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
        #making the frontend data look pretty
        eastern = pytz.timezone('US/Eastern')
        game_time_eastern = game.commence_time.astimezone(eastern)
        game.commence_time_display = game_time_eastern.strftime('%b %d, %-I:%M %p ET')
        last_update_eastern = game.last_update
        if last_update_eastern: 
            last_update_eastern = last_update_eastern.astimezone(eastern)
            last_update_eastern = last_update_eastern.strftime('%b %d, %-I:%M:%S %p ET')
        game.last_update_display = last_update_eastern

    
    return render_template('games.html', pagination=pagination, games=games, current_user=current_user)

@lines_.route('/lines/odds', methods=['GET'])
@login_required
def search_odds():
    """
    READ/GET endpoint for the odds feature
    Endpoint that allows users to query database for any odds
    Filter options: date, team 1, team 2, bookmaker, live
    Utilizes pagination to improve query efficiency and make results more digestible
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = db.session.query(Odds).join(Games).join(Bookmakers)

    #Getting query parameters
    date_query = request.args.get('date')
    team1_query = request.args.get('team1')
    team2_query = request.args.get('team2')
    bookmaker_query = request.args.get('bookmaker')
    live_query = request.args.get('live')

    #Live game implementation
    #Gets current time, and if current time is past commence time and completed not set, we know it is live 
    if live_query:
        now = datetime.now()

        one_day_earlier = now - timedelta(days=1)
        query = query.filter(
            (Games.commence_time >= one_day_earlier) & 
            (Games.commence_time < now) & 
            (Games.completed == False)
        )

    #Filtering by query parameters
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
    #Pretty up odds display (to match how American odds look with - and +)
    for odd in odds:
        odd.home_team_odds_display = odd.home_team_odds
        odd.away_team_odds_display = odd.away_team_odds
        if odd.home_team_odds > 0:
            odd.home_team_odds_display = '+'+str(odd.home_team_odds)
        if odd.away_team_odds > 0:
            odd.away_team_odds_display = '+'+str(odd.away_team_odds)

        #Making the last update time readable
        eastern = pytz.timezone('US/Eastern')
        last_update_eastern = odd.last_update
        if last_update_eastern: 
            last_update_eastern = last_update_eastern.astimezone(eastern)
            last_update_eastern = last_update_eastern.strftime('%b %d, %-I:%M:%S %p ET')
        odd.last_update_display = last_update_eastern

    return render_template('odds.html', pagination=pagination, odds=odds, current_user=current_user)

@lines_.route('/lines/arbitrage', methods=['GET'])
@login_required
def search_arbitrage():
    """
    READ/GET endpoint for the arbitrage feature
    Endpoint that allows users to query database for any arbitrage opportunity
    Filter options: date, team 1, team 2
    Utilizes pagination to improve query efficiency and make results more digestible
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10

    #Need an alias for this table since we have a home bookmaker and an away bookmaker
    AwayBookmakers = aliased(Bookmakers)

    #Joining tables to make sure we have all the data we want to present on the frontend
    #Want to show the teams, and the bookmaker (so people know where to bet that line!)
    query = db.session.query(
        ArbitrageOpportunity,
        Games,
        Bookmakers,
        AwayBookmakers
    ).join(
        Games, ArbitrageOpportunity.game_id == Games.id
    ).join(
        Bookmakers, ArbitrageOpportunity.home_odds_bookmaker_id == Bookmakers.id
    ).join(
        AwayBookmakers, ArbitrageOpportunity.away_odds_bookmaker_id == AwayBookmakers.id
    )

    #Query parameters
    date_query = request.args.get('date')
    team1_query = request.args.get('team1')
    team2_query = request.args.get('team2')
    #Filtering by query parameters
    if date_query:
        date_object = datetime.strptime(date_query, '%Y-%m-%d').date()
        query = query.filter(func.DATE(Games.commence_time) == date_object)

    if team1_query:
        query = query.filter((Games.home_team.ilike('%' + team1_query + '%')) | (Games.away_team.ilike('%' + team1_query + '%')))

    if team2_query:
        query = query.filter((Games.home_team.ilike('%' + team2_query + '%')) | (Games.away_team.ilike('%' + team2_query + '%')))
    
    #Ordering results by most recent to least recent, so that arbitrage results are most applicable and least likely to be stale
    query = query.order_by(ArbitrageOpportunity.time_found.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    arbitrages = pagination.items

    #Cleaning up display on frontend adding temporary attributes
    for arbitrage in arbitrages:
        arbitrage[0].profit_percentage_display = round(abs(arbitrage[0].profit_percentage) * 100, 2)
        arbitrage[0].home_team_odds_display = arbitrage[0].home_odds
        arbitrage[0].away_team_odds_display = arbitrage[0].away_odds
        if arbitrage[0].home_odds > 0:
            arbitrage[0].home_team_odds_display = "+"+str(arbitrage[0].home_odds)
        if arbitrage[0].away_odds > 0:
            arbitrage[0].away_team_odds_display = "+"+str(arbitrage[0].away_odds)
        
        eastern = pytz.timezone('US/Eastern')
        arbitrage_time_eastern = arbitrage[0].time_found.astimezone(eastern)
        arbitrage[0].time_found_display = arbitrage_time_eastern.strftime('%b %d, %-I:%M %p ET')

    return render_template('arbitrage.html', pagination=pagination, arbitrages=arbitrages, current_user=current_user)

@lines_.route('/insert-data', methods=['POST'])
@login_required
def call_insert_data():
    """
    Endpoint used in case we want to click a button to fetch and upsert new data instead of having the celery workers do it
    Can be useful if we don't want to spin up redis, celery beat, and celery and just want to get the new data easily but not automatically
    """
    the_odds_api.insert_data() 
    return redirect(url_for('lines.search_games'))