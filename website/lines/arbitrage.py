from website.models import Odds, ArbitrageOpportunity, Games, Bookmakers
from website import db
from sqlalchemy.orm.exc import NoResultFound


def convert_odds_to_implied(us_odds):
    if us_odds < 0: return abs(us_odds) / (abs(us_odds) + 100)
    return 100 / (us_odds + 100)

def calculate_arbitrage(odds_1, odds_2):
    return (convert_odds_to_implied(odds_1)+convert_odds_to_implied(odds_2))

def find_arbitrage(game_book_map):
    print("Finding arbitrage opportunities")
    if not game_book_map or len(game_book_map)==0: return None
    arbitrage_opps = []
    for game_id, bookmakers in game_book_map.items():
        if not game_id or not bookmakers: continue
        for bookmaker_id1, bookmaker_id2 in zip(bookmakers, bookmakers[1:]):
            if not bookmaker_id1 or not bookmaker_id2: continue

            #book 1 home, book 2 away
            try:
                odds1 = (
                    db.session.query(Odds)
                    .filter_by(game_id=game_id, bookmaker_id=bookmaker_id1)
                    .one()
                )
            except NoResultFound:
                odds1 = None

            try:
                odds2 = (
                    db.session.query(Odds)
                    .filter_by(game_id=game_id, bookmaker_id=bookmaker_id2)
                    .one()
                )
            except NoResultFound:
                odds2 = None
            if not odds1 or not odds2: continue
            arbitrage_value = calculate_arbitrage(odds1.home_team_odds, odds2.away_team_odds)
            if arbitrage_value < 1:
                #Check if this arbitrage has already been added; Fixes problem with same arbitrage opportunity being readded
                #In combination with not rescanning entire Odds table, this will speed up arbitrage finding and eliminate duplicate arbitrage opportunities
                try:
                    already_found_arbitrage = (db.session.query(ArbitrageOpportunity).filter_by(game_id=game_id, home_team_odds_id=odds1.id, away_team_odds_id=odds2.id, profit_percentage=arbitrage_value-1).one())
                except NoResultFound:
                    arbitrage_opp = ArbitrageOpportunity(game_id=odds1.game_id, home_team_odds_id=odds1.id, away_team_odds_id=odds2.id, profit_percentage=arbitrage_value-1)
                    arbitrage_opps.append(arbitrage_opp)

            #book 1 away, book 2 home
            arbitrage_value = calculate_arbitrage(odds2.home_team_odds, odds1.away_team_odds)
            if arbitrage_value < 1:
                try:
                    already_found_arbitrage = (db.session.query(ArbitrageOpportunity).filter_by(game_id=game_id, home_team_odds_id=odds2.id, away_team_odds_id=odds1.id, profit_percentage=1-arbitrage_value).one())
                except NoResultFound:
                    arbitrage_opp = ArbitrageOpportunity(game_id=odds1.game_id, home_team_odds_id=odds2.id, away_team_odds_id=odds1.id, profit_percentage=1-arbitrage_value)
                    arbitrage_opps.append(arbitrage_opp)
                
    print("Finished finding arbitrage opportunities")
    return arbitrage_opps

def insert_arbitrage(game_book_map):
    arbitrage_opps = find_arbitrage(game_book_map)
    db.session.add_all(arbitrage_opps)
    db.session.commit()
    print("Finished adding arbitrage opportunities")