import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from website import db
from dotenv import load_dotenv
from website.models import Games, Bookmakers, Odds
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm.exc import NoResultFound
from . import arbitrage
from celery import shared_task
from collections import defaultdict

#File with utility functions for fetching and upserting data from the odds api

#loading environment variables
load_dotenv()

#getting API key, and other platform specific criteria we have opted for
API_KEY = os.getenv("API_KEY")
MARKETS = "h2h"
REGIONS = "us"
ODDS_FORMAT = "american"
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
        #Get request following The Odds API standard for data in our sports for game scores
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

def get_odds_api_data():
    """
    We want odds from yesterday and in the future
    Don't want odds from earlier than that because those games have already ended
    Going to the previous day is so that if games go over midnight, we still check for those odds
    """
    current_date = datetime.now()
    previous_day = current_date - timedelta(days=1)
    previous_day_start = previous_day.replace(hour=0, minute=0, second=0, microsecond=0)
    commence_time_from = previous_day_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    data_list = []
    for sport in SPORTS:
        #Get request with query parameters
        request_url = "https://api.the-odds-api.com/v4/sports/{sport}/odds?apiKey={api_key}&regions={regions}&markets={markets}&dateFormat=iso&oddsFormat={odds_format}&commenceTimeFrom={commence_time_from}".format(
        sport=sport,
        api_key=API_KEY,
        markets=MARKETS,
        regions=REGIONS,
        odds_format=ODDS_FORMAT,
        commence_time_from=commence_time_from
        )
        response = requests.get(request_url)
        data = response.json()
        data_list.append(data)
    return data_list



#---------------------------- THE ODDS API DATA PIPELINE ------------------------------------------

#Celery task to be run asynchronously to fetch data from Odds API
@shared_task(ignore_result=False)
def insert_data():
    """
    1. First fetches games from the odds api
    2. Then fetches odds from the odds api
    3. Now that we have data from the odds api for games and odds, find arbitrage opps

    - Asynchronous job run by celery worker, scheduled with celery beat
    - Run every 5 minutes to ensure frequent updates to live games, odds, and best arbitrage chances
    """
    print("Fetching new game data")
    data_list = get_games_api_data()
    if not data_list:
        return
    for data in data_list:
        if not data: continue
        for item in data:
            home_score, away_score = extract_scores(item)
            item['home_team_score'] = home_score
            item['away_team_score'] = away_score

            #create insert statement with data obtained from odds api after parsing
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
        
            #update dictionary on attributes that may need to be updated if game id already exists in db
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

            #allows for upsert, checks if game already exists and does update instead of inserting
            stmt = stmt.on_conflict_do_update(
                index_elements=[Games.id],
                set_=update_dict,
                where=(Games.last_update.is_(None) | ((item['last_update'] is not None) and (Games.last_update < item['last_update'])))
            )

            db.session.execute(stmt)
    db.session.commit()
    print("Finished adding game data")
    #Once games have been updated/inserted, now check odds
    #This order is important because we don't want odds for games that don't exist in our db yet
    insert_odds()

def insert_odds():
    """
    - Fetch odds from the odds api
    - Match them with a game id that should exist in our database (if not, ignore it)
    - Once we finish fetching odds, let's find arbitrage
    """
    print("Fetching new odds data")
    data_list = get_odds_api_data()

    #Dictionary used to map game id to a list of bookmakers, that will eventually be used to find arbitrage
    game_book_map = defaultdict(list)
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
                            
                        #create insert statement with data obtained from odds api after parsing
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

                        #update dictionary on attributes that may need to be updated if odds already exists in db with same game and bookmaker
                        update_dict = {
                            Odds.home_team_odds: home_team_odds,
                            Odds.away_team_odds: away_team_odds,
                            Odds.draw_odds: draw_odds,
                            Odds.last_update: market['last_update']
                        }

                        #Notice in the where, we only update if the last_update is none in our db, or if the new last_update we obtained is more recent than in db
                        stmt = stmt.on_conflict_do_update(
                            index_elements=[Odds.game_id, Odds.bookmaker_id],
                            set_=update_dict,
                            where=(Odds.last_update.is_(None) | ((market['last_update'] is not None) and (Odds.last_update < market['last_update'])))
                        )

                        game_book_map[game_id].append(bookmaker_obj.id)
                        db.session.execute(stmt)

    db.session.commit()
    print("Finished adding new odds data")

    #Now that we have fetched and added odds to our db, let's find our arbitrage opportunities
    arbitrage.insert_arbitrage(game_book_map)


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

